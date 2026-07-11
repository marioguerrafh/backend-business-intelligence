from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.modules.rule.application.condition_evaluator import evaluate_condition, parse_condition
from app.modules.rule.application.contracts import ExecuteRulesCommand, ExecuteRulesResult
from app.modules.rule.domain.entities import RuleExecutionResult
from app.modules.rule.domain.errors import RuleCatalogValidationError, RuleConditionSyntaxError, RuleEvaluationError
from app.modules.rule.infrastructure.rule_catalog_yaml import YamlRuleCatalogReader


@dataclass(slots=True)
class ExecuteRulesUseCase:
    repository: object
    catalog_reader: YamlRuleCatalogReader

    def execute(self, command: ExecuteRulesCommand) -> ExecuteRulesResult:
        rules = self.catalog_reader.load_rules()
        kpis = self.repository.load_kpis_for_period(company_id=command.company_id, period_ref=command.period_ref)
        kpi_by_id = {item.kpi_id: item.value for item in kpis}

        evaluated = 0
        fired = 0
        idempotent = 0
        event_ids: list[str] = []

        for rule in rules:
            if not rule.enabled:
                continue
            if rule.kpi_id not in kpi_by_id:
                continue

            evaluated += 1
            if self.repository.has_rule_result(
                company_id=command.company_id,
                period_ref=command.period_ref,
                kpi_id=rule.kpi_id,
                rule_id=rule.rule_id,
            ):
                idempotent += 1
                self.repository.add_audit(
                    company_id=command.company_id,
                    period_ref=command.period_ref,
                    kpi_id=rule.kpi_id,
                    rule_id=rule.rule_id,
                    status="idempotent",
                    expression=rule.condition,
                    trace=["dedup hit"],
                    fired=False,
                    orchestrator_run_id=command.orchestrator_run_id,
                    error_message=None,
                )
                continue

            metric_value = float(kpi_by_id[rule.kpi_id])
            history = self.repository.load_kpi_history(
                company_id=command.company_id,
                kpi_id=rule.kpi_id,
                upto_period_ref=command.period_ref,
                limit=36,
            )
            trace: list[str] = []

            try:
                ast = parse_condition(rule.condition)
                is_fired = evaluate_condition(ast, metric_value=metric_value, history=history, trace=trace)
            except (RuleConditionSyntaxError, RuleEvaluationError, RuleCatalogValidationError) as exc:
                self.repository.add_audit(
                    company_id=command.company_id,
                    period_ref=command.period_ref,
                    kpi_id=rule.kpi_id,
                    rule_id=rule.rule_id,
                    status="failed",
                    expression=rule.condition,
                    trace=trace,
                    fired=False,
                    orchestrator_run_id=command.orchestrator_run_id,
                    error_message=str(exc),
                )
                continue

            if not is_fired:
                self.repository.add_audit(
                    company_id=command.company_id,
                    period_ref=command.period_ref,
                    kpi_id=rule.kpi_id,
                    rule_id=rule.rule_id,
                    status="evaluated",
                    expression=rule.condition,
                    trace=trace,
                    fired=False,
                    orchestrator_run_id=command.orchestrator_run_id,
                    error_message=None,
                )
                continue

            fired += 1
            alert = RuleExecutionResult(
                alert_id=f"rule_{uuid4().hex[:16]}",
                rule_id=rule.rule_id,
                kpi_id=rule.kpi_id,
                company_id=command.company_id,
                period_ref=command.period_ref,
                severity=rule.severity,
                priority=rule.priority,
                title=f"{rule.kpi_id} - {rule.name}",
                description=f"Rule {rule.rule_id} fired for KPI {rule.kpi_id} with value {metric_value}",
                metric_value=metric_value,
                fired_at=datetime.now(timezone.utc),
                orchestrator_run_id=command.orchestrator_run_id,
            )
            alert_id = self.repository.save_rule_result(alert)
            self.repository.add_audit(
                company_id=command.company_id,
                period_ref=command.period_ref,
                kpi_id=rule.kpi_id,
                rule_id=rule.rule_id,
                status="fired",
                expression=rule.condition,
                trace=trace,
                fired=True,
                orchestrator_run_id=command.orchestrator_run_id,
                error_message=None,
            )
            event_id = self.repository.publish_rule_executed(
                payload={
                    "company_id": command.company_id,
                    "period_ref": command.period_ref,
                    "rule_id": rule.rule_id,
                    "kpi_id": rule.kpi_id,
                    "severity": rule.severity,
                    "priority": rule.priority,
                    "alert_id": alert_id,
                    "orchestrator_run_id": command.orchestrator_run_id,
                    "source_event_id": command.source_event_id,
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            event_ids.append(event_id)

        return ExecuteRulesResult(
            company_id=command.company_id,
            period_ref=command.period_ref,
            orchestrator_run_id=command.orchestrator_run_id,
            evaluated_rules=evaluated,
            fired_rules=fired,
            idempotent_hits=idempotent,
            published_event_ids=tuple(event_ids),
        )
