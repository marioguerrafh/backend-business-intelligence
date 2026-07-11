from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RecommendationPrioritizer:
    def effort_score(self, effort_level: str) -> float:
        lowered = effort_level.lower().strip()
        if lowered == "low":
            return 0.90
        if lowered == "medium":
            return 0.60
        if lowered == "high":
            return 0.35
        return 0.50

    def urgency_score(self, *, severity: str, sla_target: str) -> float:
        sev = severity.upper().strip()
        base = {
            "CRITICAL": 1.00,
            "HIGH": 0.85,
            "MEDIUM": 0.65,
            "LOW": 0.45,
            "INFO": 0.30,
        }.get(sev, 0.40)

        sla = sla_target.lower().strip()
        if sla.endswith("h"):
            try:
                hours = float(sla[:-1])
                if hours <= 12:
                    return min(1.0, base + 0.10)
                if hours <= 24:
                    return min(1.0, base + 0.05)
            except ValueError:
                pass
        return base

    def impact_score(self, expected_impact_value: float) -> float:
        # Normalization to [0, 1] with soft cap for outliers.
        if expected_impact_value <= 0:
            return 0.0
        return min(1.0, expected_impact_value / 100000.0)

    def rank_score(
        self,
        *,
        impact_score: float,
        urgency_score: float,
        effort_score: float,
        confidence_score: float,
    ) -> float:
        # Higher effort should reduce priority.
        raw = (impact_score * 0.45) + (urgency_score * 0.35) + ((1.0 - effort_score) * 0.10) + (confidence_score * 0.10)
        return round(max(0.0, min(1.0, raw)), 6)
