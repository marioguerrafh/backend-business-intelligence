from dataclasses import dataclass

from app.modules.insight.application.contracts import GenerateInsightsCommand
from app.modules.insight.application.template_renderer import InsightTemplateRenderer
from app.modules.insight.application.use_cases import GenerateInsightsUseCase
from app.modules.insight.domain.entities import PromptTemplateDefinition


@dataclass
class _FakePromptCatalog:
    def load_prompts(self):
        return (
            PromptTemplateDefinition(
                prompt_id="p.exec.health",
                intent="executive_summary",
                audience="c_level",
                language="pt-BR",
                output_schema="executive_summary",
                guardrails=("no_cross_tenant_data",),
            ),
        )


@dataclass
class _FakeRepo:
    dedup: bool = False

    def __post_init__(self):
        self.saved = []
        self.audits = []
        self.events = []

    def load_kpi_context(self, *, company_id: str, period_ref: str):
        return {"FIN_01": 120.0, "FIN_02": 30.0, "FIN_03": -50.0, "EXE_04": 67.0}

    def load_fired_rule_ids(self, *, company_id: str, period_ref: str):
        return ("r.fin03.cash_negative_3d",)

    def load_top_recommendation_ids(self, *, company_id: str, period_ref: str, limit: int = 3):
        return ("rec.cash.001",)

    def has_insight(self, *, company_id: str, period_ref: str, insight_type: str):
        return self.dedup

    def save_insight(self, insight):
        self.saved.append(insight)

    def add_audit(self, **kwargs):
        self.audits.append(kwargs)

    def publish_insight_generated(self, *, payload):
        event_id = f"evt_{len(self.events) + 1}"
        self.events.append((event_id, payload))
        return event_id


def test_insight_use_case_generates_from_templates() -> None:
    repo = _FakeRepo(dedup=False)
    use_case = GenerateInsightsUseCase(
        repository=repo,
        prompt_catalog=_FakePromptCatalog(),
        renderer=InsightTemplateRenderer(),
    )

    result = use_case.execute(
        GenerateInsightsCommand(
            company_id="cmp_acme",
            period_ref="2026-07",
            orchestrator_run_id="run_ins_1",
        )
    )

    assert result.generated_count == 1
    assert len(result.published_event_ids) == 1


def test_insight_use_case_honors_dedup() -> None:
    repo = _FakeRepo(dedup=True)
    use_case = GenerateInsightsUseCase(
        repository=repo,
        prompt_catalog=_FakePromptCatalog(),
        renderer=InsightTemplateRenderer(),
    )

    result = use_case.execute(
        GenerateInsightsCommand(
            company_id="cmp_acme",
            period_ref="2026-07",
            orchestrator_run_id="run_ins_1",
        )
    )

    assert result.generated_count == 0
    assert result.published_event_ids == ()
