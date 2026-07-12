from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.modules.rule.application.condition_evaluator import parse_condition
from app.modules.rule.domain.entities import RuleDefinition
from app.modules.rule.domain.errors import RuleCatalogValidationError


@dataclass(slots=True)
class _CatalogCache:
    path: Path
    mtime_ns: int
    rules: tuple[RuleDefinition, ...]


_CACHE: _CatalogCache | None = None


class YamlRuleCatalogReader:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or self._module_local_path("rule-dsl.v1.yaml")

    def load_rules(self) -> tuple[RuleDefinition, ...]:
        global _CACHE

        path = self._resolve_path()
        stat = path.stat()
        if _CACHE and _CACHE.path == path and _CACHE.mtime_ns == stat.st_mtime_ns:
            return _CACHE.rules

        with path.open("r", encoding="utf-8") as fp:
            payload = yaml.safe_load(fp) or {}

        raw_rules = payload.get("rule_examples", [])
        if not isinstance(raw_rules, list) or not raw_rules:
            raise RuleCatalogValidationError("rule catalog is empty")

        rules: list[RuleDefinition] = []
        for item in raw_rules:
            rules.append(self._build_rule(item))

        _CACHE = _CatalogCache(path=path, mtime_ns=stat.st_mtime_ns, rules=tuple(rules))
        return _CACHE.rules

    def _build_rule(self, item: dict[str, Any]) -> RuleDefinition:
        required = ["rule_id", "kpi_id", "name", "condition", "severity", "priority", "enabled"]
        missing = [k for k in required if k not in item]
        if missing:
            raise RuleCatalogValidationError(f"rule missing required fields: {', '.join(missing)}")

        severity = str(item["severity"]).strip().upper()
        if severity not in {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            raise RuleCatalogValidationError(f"invalid severity '{item['severity']}'")

        priority = str(item["priority"]).strip().lower()
        if priority not in {"p0", "p1", "p2", "p3"}:
            raise RuleCatalogValidationError(f"invalid priority '{item['priority']}'")

        condition = str(item["condition"]).strip()
        parse_condition(condition)

        return RuleDefinition(
            rule_id=str(item["rule_id"]).strip(),
            kpi_id=str(item["kpi_id"]).strip(),
            name=str(item["name"]).strip(),
            condition=condition,
            severity=severity,
            priority=priority,
            enabled=bool(item["enabled"]),
        )

    def _resolve_path(self) -> Path:
        if self.path.exists():
            return self.path
        fallback = Path(__file__).resolve().parent / "rule-dsl.v1.yaml"
        if fallback.exists():
            return fallback
        raise RuleCatalogValidationError(f"rule catalog file not found: {self.path}")

    def _default_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parents[4] / "docs" / "semantic-layer" / filename

    def _module_local_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parent / filename
