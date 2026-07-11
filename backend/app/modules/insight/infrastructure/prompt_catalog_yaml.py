from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from app.modules.insight.domain.entities import PromptTemplateDefinition
from app.modules.insight.domain.errors import InsightCatalogValidationError


@dataclass(slots=True)
class _CatalogCache:
    path: Path
    mtime_ns: int
    prompts: tuple[PromptTemplateDefinition, ...]


_CACHE: _CatalogCache | None = None


class YamlPromptCatalogReader:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or self._default_path("ai-prompt-dsl.v1.yaml")

    def load_prompts(self) -> tuple[PromptTemplateDefinition, ...]:
        global _CACHE

        path = self._resolve_path()
        stat = path.stat()
        if _CACHE and _CACHE.path == path and _CACHE.mtime_ns == stat.st_mtime_ns:
            return _CACHE.prompts

        with path.open("r", encoding="utf-8") as fp:
            payload = yaml.safe_load(fp) or {}

        examples = payload.get("prompt_examples", [])
        if not isinstance(examples, list) or not examples:
            raise InsightCatalogValidationError("prompt catalog is empty")

        prompts: list[PromptTemplateDefinition] = []
        for item in examples:
            prompt_id = str(item.get("prompt_id") or "").strip()
            intent = str(item.get("intent") or "").strip()
            audience = str(item.get("audience") or "").strip()
            language = str(item.get("language") or "pt-BR").strip()
            output_schema = str(item.get("output_schema") or "executive_summary").strip()
            guardrails = tuple(str(rule).strip() for rule in item.get("guardrails") or [])

            if not prompt_id or not intent:
                raise InsightCatalogValidationError("prompt_id and intent are required")

            prompts.append(
                PromptTemplateDefinition(
                    prompt_id=prompt_id,
                    intent=intent,
                    audience=audience,
                    language=language,
                    output_schema=output_schema,
                    guardrails=guardrails,
                )
            )

        _CACHE = _CatalogCache(path=path, mtime_ns=stat.st_mtime_ns, prompts=tuple(prompts))
        return _CACHE.prompts

    def _resolve_path(self) -> Path:
        if self.path.exists():
            return self.path
        fallback = Path(__file__).resolve().parent / "ai-prompt-dsl.v1.yaml"
        if fallback.exists():
            return fallback
        raise InsightCatalogValidationError(f"prompt catalog file not found: {self.path}")

    def _default_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parents[4] / "docs" / "semantic-layer" / filename
