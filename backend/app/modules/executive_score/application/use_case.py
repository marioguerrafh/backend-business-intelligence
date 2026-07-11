from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.modules.executive_score.application.contracts import (
    CalculateExecutiveScoreCommand,
    CalculateExecutiveScoreResult,
)
from app.modules.executive_score.application.score_calculator import ExecutiveScoreCalculator
from app.modules.executive_score.domain.entities import ExecutiveScoreAggregate, ScoreInputs


@dataclass(slots=True)
class CalculateExecutiveScoreUseCase:
    repository: object
    calculator: ExecutiveScoreCalculator

    def execute(self, command: CalculateExecutiveScoreCommand) -> CalculateExecutiveScoreResult:
        kpis = self.repository.load_kpis_for_period(company_id=command.company_id, period_ref=command.period_ref)
        rule_penalty = self.repository.compute_rule_penalty(company_id=command.company_id, period_ref=command.period_ref)
        recommendation_bonus = self.repository.compute_recommendation_bonus(
            company_id=command.company_id,
            period_ref=command.period_ref,
        )

        inputs = ScoreInputs(
            financial_values=tuple(self._normalize_to_score(value) for key, value in kpis.items() if key.startswith("FIN-")),
            commercial_values=tuple(self._normalize_to_score(value) for key, value in kpis.items() if key.startswith("COM-")),
            operational_values=tuple(self._normalize_to_score(value) for key, value in kpis.items() if key.startswith("OPR-")),
            inventory_values=tuple(self._normalize_to_score(value) for key, value in kpis.items() if key.startswith("EST-")),
            rule_penalty=rule_penalty,
            recommendation_bonus=recommendation_bonus,
        )

        financial, commercial, operational, inventory, executive = self.calculator.calculate(inputs)
        aggregate = ExecutiveScoreAggregate(
            executive_score_id=f"esc_{uuid4().hex[:16]}",
            company_id=command.company_id,
            period_ref=command.period_ref,
            financial_score=financial,
            commercial_score=commercial,
            operational_score=operational,
            inventory_score=inventory,
            executive_score=executive,
            score_version="v1",
            calculated_at=datetime.now(timezone.utc),
            orchestrator_run_id=command.orchestrator_run_id,
        )

        self.repository.save_executive_score(aggregate)
        self.repository.save_timeline_snapshot(
            company_id=aggregate.company_id,
            period_ref=aggregate.period_ref,
            financial_score=aggregate.financial_score,
            commercial_score=aggregate.commercial_score,
            operational_score=aggregate.operational_score,
            executive_score=aggregate.executive_score,
        )
        self.repository.add_audit(
            company_id=aggregate.company_id,
            period_ref=aggregate.period_ref,
            status="calculated",
            details={
                "financial_score": financial,
                "commercial_score": commercial,
                "operational_score": operational,
                "inventory_score": inventory,
                "executive_score": executive,
                "rule_penalty": rule_penalty,
                "recommendation_bonus": recommendation_bonus,
            },
            orchestrator_run_id=command.orchestrator_run_id,
        )

        event_id = self.repository.publish_executive_score_updated(
            payload={
                "company_id": aggregate.company_id,
                "period_ref": aggregate.period_ref,
                "financial_score": aggregate.financial_score,
                "commercial_score": aggregate.commercial_score,
                "operational_score": aggregate.operational_score,
                "inventory_score": aggregate.inventory_score,
                "executive_score": aggregate.executive_score,
                "orchestrator_run_id": aggregate.orchestrator_run_id,
                "source_event_id": command.source_event_id,
            }
        )

        return CalculateExecutiveScoreResult(
            company_id=aggregate.company_id,
            period_ref=aggregate.period_ref,
            orchestrator_run_id=aggregate.orchestrator_run_id,
            financial_score=aggregate.financial_score,
            commercial_score=aggregate.commercial_score,
            operational_score=aggregate.operational_score,
            inventory_score=aggregate.inventory_score,
            executive_score=aggregate.executive_score,
            published_event_id=event_id,
        )

    def _normalize_to_score(self, value: float) -> float:
        # Converts arbitrary KPI value to a bounded score scale.
        if value <= 0:
            return 0.0
        if value >= 100:
            return 100.0
        return float(value)
