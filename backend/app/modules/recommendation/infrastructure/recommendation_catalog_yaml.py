from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.modules.recommendation.application.dsl_evaluator import eval_expression
from app.modules.recommendation.domain.entities import RecommendationDefinition
from app.modules.recommendation.domain.errors import RecommendationCatalogValidationError


@dataclass(slots=True)
class _CatalogCache:
    path: Path
    mtime_ns: int
    definitions: tuple[RecommendationDefinition, ...]


_CACHE: _CatalogCache | None = None


class YamlRecommendationCatalogReader:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or self._default_path("recommendation-dsl.v1.yaml")

    def load_recommendations(self) -> tuple[RecommendationDefinition, ...]:
        global _CACHE

        path = self._resolve_path()
        stat = path.stat()
        if _CACHE and _CACHE.path == path and _CACHE.mtime_ns == stat.st_mtime_ns:
            return _CACHE.definitions

        with path.open("r", encoding="utf-8") as fp:
            payload = yaml.safe_load(fp) or {}

        examples = payload.get("recommendation_examples", [])
        if not isinstance(examples, list) or not examples:
            raise RecommendationCatalogValidationError("recommendation catalog is empty")

        definitions = tuple(self._build_definition(item) for item in examples)
        _CACHE = _CatalogCache(path=path, mtime_ns=stat.st_mtime_ns, definitions=definitions)
        return definitions

    def _build_definition(self, item: dict[str, Any]) -> RecommendationDefinition:
        required = [
            "recommendation_id",
            "name",
            "trigger_ref",
            "impact_model",
            "effort_level",
            "confidence_score",
            "owner_role",
            "sla_target",
            "message_template",
            "action_playbook",
            "enabled",
        ]
        missing = [key for key in required if key not in item]
        if missing:
            raise RecommendationCatalogValidationError(
                f"recommendation missing required fields: {', '.join(missing)}"
            )

        trigger_ref = item.get("trigger_ref") or {}
        trigger_rule_id = str(trigger_ref.get("rule_id") or "").strip()
        if not trigger_rule_id:
            raise RecommendationCatalogValidationError("trigger_ref.rule_id is required")

        impact_model = item.get("impact_model") or {}
        expected_impact_formula = str(impact_model.get("expected_impact_formula") or "").strip()
        if not expected_impact_formula:
            raise RecommendationCatalogValidationError("impact_model.expected_impact_formula is required")

        # Validate expression syntax and supported function names early.
        eval_expression(expected_impact_formula, {})

        conditions = tuple(str(c).strip() for c in item.get("applicability_conditions") or [])
        for condition in conditions:
            if condition:
                eval_expression(condition, {})

        effort_level = str(item["effort_level"]).strip().lower()
        if effort_level not in {"low", "medium", "high"}:
            raise RecommendationCatalogValidationError(f"invalid effort_level '{item['effort_level']}'")

        confidence_score = float(item["confidence_score"])
        if confidence_score < 0.0 or confidence_score > 1.0:
            raise RecommendationCatalogValidationError("confidence_score must be between 0 and 1")

        return RecommendationDefinition(
            recommendation_id=str(item["recommendation_id"]).strip(),
            name=str(item["name"]).strip(),
            trigger_rule_id=trigger_rule_id,
            applicability_conditions=conditions,
            expected_impact_formula=expected_impact_formula,
            expected_impact_unit=str(impact_model.get("expected_impact_unit") or "unit").strip(),
            impact_horizon=str(impact_model.get("impact_horizon") or "7d").strip(),
            effort_level=effort_level,
            confidence_score=confidence_score,
            owner_role=str(item["owner_role"]).strip(),
            sla_target=str(item["sla_target"]).strip(),
            message_template=str(item["message_template"]).strip(),
            action_playbook=tuple(str(step).strip() for step in item.get("action_playbook") or []),
            enabled=bool(item["enabled"]),
        )

    def _resolve_path(self) -> Path:
        if self.path.exists():
            return self.path
        fallback = Path(__file__).resolve().parent / "recommendation-dsl.v1.yaml"
        if fallback.exists():
            return fallback
        raise RecommendationCatalogValidationError(f"recommendation catalog file not found: {self.path}")

    def _default_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parents[4] / "docs" / "semantic-layer" / filename
