from dataclasses import dataclass

from app.modules.recommendation.application.contracts import GenerateRecommendationsCommand
from app.modules.recommendation.application.recommendation_builder import RecommendationBuilder
from app.modules.recommendation.application.recommendation_publisher import RecommendationPublisher
from app.modules.recommendation.application.recommendation_prioritizer import RecommendationPrioritizer
from app.modules.recommendation.application.recommendation_service import RecommendationService
from app.modules.recommendation.application.use_cases import GenerateRecommendationsUseCase
from app.modules.recommendation.domain.entities import RecommendationDefinition


@dataclass
class _FakeCatalog:
    def load_recommendations(self):
        return (
            RecommendationDefinition(
                recommendation_id="rec.cash.001",
                name="acelerar_recebiveis_criticos",
                trigger_rule_id="r.fin03.cash_negative_3d",
                applicability_conditions=("gt(open_receivables_over_30d,0)",),
                expected_impact_formula="mul(open_receivables_over_30d, collection_success_rate)",
                expected_impact_unit="BRL",
                impact_horizon="7d",
                effort_level="medium",
                confidence_score=0.82,
                owner_role="treasury_manager",
                sla_target="48h",
                message_template="Impacto {expected_impact_value} em {impact_horizon}",
                action_playbook=("step_1",),
                enabled=True,
            ),
        )


@dataclass
class _RuleSignal:
    rule_id: str
    severity: str
    priority: str
    metric_value: float


@dataclass
class _FakeRepo:
    has_dedup: bool = False

    def __post_init__(self):
        self.saved = []
        self.audits = []
        self.events = []

    def load_kpi_context(self, *, company_id: str, period_ref: str):
        return {"open_receivables_over_30d": 1000.0, "collection_success_rate": 0.5}

    def load_rule_results(self, *, company_id: str, period_ref: str):
        return (_RuleSignal("r.fin03.cash_negative_3d", "HIGH", "p0", -100.0),)

    def has_recommendation_result(self, *, company_id: str, period_ref: str, recommendation_id: str):
        return self.has_dedup

    def save_recommendation_result(self, recommendation):
        self.saved.append(recommendation)

    def add_audit(self, **kwargs):
        self.audits.append(kwargs)

    def publish_recommendation_generated(self, *, payload):
        event_id = f"evt_{len(self.events) + 1}"
        self.events.append((event_id, payload))
        return event_id


def test_recommendation_use_case_generates_and_publishes() -> None:
    repo = _FakeRepo(has_dedup=False)
    use_case = GenerateRecommendationsUseCase(
        catalog_reader=_FakeCatalog(),
        service=RecommendationService(
            repository=repo,
            builder=RecommendationBuilder(),
            prioritizer=RecommendationPrioritizer(),
            publisher=RecommendationPublisher(repository=repo),
        ),
    )

    result = use_case.execute(
        GenerateRecommendationsCommand(
            company_id="cmp_acme",
            period_ref="2026-07",
            orchestrator_run_id="run_rec_1",
        )
    )

    assert result.generated_count == 1
    assert result.deduplicated_count == 0
    assert result.grouped_count == 1
    assert len(result.published_event_ids) == 1


def test_recommendation_use_case_honors_dedup() -> None:
    repo = _FakeRepo(has_dedup=True)
    use_case = GenerateRecommendationsUseCase(
        catalog_reader=_FakeCatalog(),
        service=RecommendationService(
            repository=repo,
            builder=RecommendationBuilder(),
            prioritizer=RecommendationPrioritizer(),
            publisher=RecommendationPublisher(repository=repo),
        ),
    )

    result = use_case.execute(
        GenerateRecommendationsCommand(
            company_id="cmp_acme",
            period_ref="2026-07",
            orchestrator_run_id="run_rec_1",
        )
    )

    assert result.generated_count == 0
    assert result.deduplicated_count == 1
    assert len(repo.saved) == 0
