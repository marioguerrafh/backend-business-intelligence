from __future__ import annotations

from dataclasses import dataclass

from app.modules.executive_score.domain.entities import ScoreInputs


@dataclass(slots=True)
class ExecutiveScoreCalculator:
    def calculate(self, inputs: ScoreInputs) -> tuple[float, float, float, float, float]:
        financial = self._avg_or_default(inputs.financial_values)
        commercial = self._avg_or_default(inputs.commercial_values)
        operational = self._avg_or_default(inputs.operational_values)
        inventory = self._avg_or_default(inputs.inventory_values)

        base = (
            (financial * 0.35)
            + (commercial * 0.25)
            + (operational * 0.20)
            + (inventory * 0.20)
        )

        executive = base - inputs.rule_penalty + inputs.recommendation_bonus
        executive = self._clamp(executive)

        return (
            self._clamp(financial),
            self._clamp(commercial),
            self._clamp(operational),
            self._clamp(inventory),
            round(executive, 4),
        )

    def _avg_or_default(self, values: tuple[float, ...]) -> float:
        if not values:
            return 70.0
        return round(sum(values) / len(values), 4)

    def _clamp(self, value: float) -> float:
        if value < 0:
            return 0.0
        if value > 100:
            return 100.0
        return round(value, 4)
