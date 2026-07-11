from dataclasses import dataclass

from app.modules.rule.application.contracts import ExecuteRulesCommand
from app.modules.rule.application.use_case import ExecuteRulesUseCase
from app.modules.rule.domain.entities import KPIValue, RuleDefinition


@dataclass
class _FakeCatalog:
    def load_rules(self):
        return (
            RuleDefinition(
                rule_id="r.fin03.cash_negative_3d",
                kpi_id="FIN-03",
                name="cash_negativo",
                condition="and(lt(metric_value,0), consecutive_periods(3, day))",
                severity="HIGH",
                priority="p0",
                enabled=True,
            ),
        )


@dataclass
class _FakeRepo:
    dedup: bool = False

    def __post_init__(self):
        self.saved = []
        self.audits = []
        self.events = []

    def load_kpis_for_period(self, *, company_id: str, period_ref: str):
        return [KPIValue(kpi_id="FIN-03", value=-10.0)]

    def load_kpi_history(self, *, company_id: str, kpi_id: str, upto_period_ref: str, limit: int = 36):
        return [-3.0, -5.0, -10.0]

    def has_rule_result(self, *, company_id: str, period_ref: str, kpi_id: str, rule_id: str):
        return self.dedup

    def save_rule_result(self, result):
        self.saved.append(result)
        return result.alert_id

    def add_audit(self, **kwargs):
        self.audits.append(kwargs)

    def publish_rule_executed(self, *, payload: dict[str, object]):
        event_id = f"evt_{len(self.events)+1}"
        self.events.append((event_id, payload))
        return event_id


def test_rule_use_case_fires_alert_and_publishes_event() -> None:
    repo = _FakeRepo(dedup=False)
    use_case = ExecuteRulesUseCase(repository=repo, catalog_reader=_FakeCatalog())

    result = use_case.execute(
        ExecuteRulesCommand(
            company_id="cmp_acme",
            period_ref="2026-07",
            orchestrator_run_id="run_rule_1",
        )
    )

    assert result.evaluated_rules == 1
    assert result.fired_rules == 1
    assert result.idempotent_hits == 0
    assert len(repo.saved) == 1
    assert len(repo.events) == 1


def test_rule_use_case_honors_idempotency() -> None:
    repo = _FakeRepo(dedup=True)
    use_case = ExecuteRulesUseCase(repository=repo, catalog_reader=_FakeCatalog())

    result = use_case.execute(
        ExecuteRulesCommand(
            company_id="cmp_acme",
            period_ref="2026-07",
            orchestrator_run_id="run_rule_1",
        )
    )

    assert result.evaluated_rules == 1
    assert result.fired_rules == 0
    assert result.idempotent_hits == 1
    assert repo.saved == []
