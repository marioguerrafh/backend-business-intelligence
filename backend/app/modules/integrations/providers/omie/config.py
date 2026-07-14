from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True, frozen=True)
class OmieProviderConfig:
    max_requests_per_minute_ip: int = 960
    max_requests_per_method: int = 240
    max_parallel_requests: int = 4
    page_size_max: int = 500
    cache_ttl_seconds: int = 60
    retry_attempts: int = 5
    backoff_base_seconds: float = 1.0
    backoff_max_seconds: float = 16.0
    connection_timeout: float = 30.0
    read_timeout: float = 60.0
    write_timeout: float = 30.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 300.0
    http_425_cooldown_seconds: float = 60.0


def _to_int(raw: Any, default: int) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _to_float(raw: Any, default: float) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _default_config_path() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "provider_config.yaml"
        if candidate.exists():
            return candidate
    return Path(__file__).resolve().parents[5] / "provider_config.yaml"


def load_omie_provider_config(config_path: str | Path | None = None) -> OmieProviderConfig:
    path = Path(config_path) if config_path is not None else _default_config_path()

    if not path.exists():
        return OmieProviderConfig()

    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return OmieProviderConfig()

    root = loaded if isinstance(loaded, dict) else {}
    omie = root.get("omie") if isinstance(root.get("omie"), dict) else {}

    return OmieProviderConfig(
        max_requests_per_minute_ip=_to_int(omie.get("max_requests_per_minute_ip"), 960),
        max_requests_per_method=_to_int(omie.get("max_requests_per_method"), 240),
        max_parallel_requests=_to_int(omie.get("max_parallel_requests"), 4),
        page_size_max=_to_int(omie.get("page_size_max"), 500),
        cache_ttl_seconds=_to_int(omie.get("cache_ttl_seconds"), 60),
        retry_attempts=_to_int(omie.get("retry_attempts"), 5),
        backoff_base_seconds=_to_float(omie.get("backoff_base_seconds"), 1.0),
        backoff_max_seconds=_to_float(omie.get("backoff_max_seconds"), 16.0),
        connection_timeout=_to_float(omie.get("connection_timeout"), 30.0),
        read_timeout=_to_float(omie.get("read_timeout"), 60.0),
        write_timeout=_to_float(omie.get("write_timeout"), 30.0),
        circuit_breaker_threshold=_to_int(omie.get("circuit_breaker_threshold"), 5),
        circuit_breaker_timeout=_to_float(omie.get("circuit_breaker_timeout"), 300.0),
        http_425_cooldown_seconds=_to_float(omie.get("http_425_cooldown_seconds"), 60.0),
    )
