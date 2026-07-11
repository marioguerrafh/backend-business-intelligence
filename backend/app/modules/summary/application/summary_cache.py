from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock


@dataclass(slots=True)
class SummaryCacheItem:
    payload: dict[str, object]
    expires_at: datetime


class SummaryCache:
    def get(self, key: str) -> dict[str, object] | None:
        raise NotImplementedError

    def set(self, key: str, payload: dict[str, object]) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class InMemorySummaryCache(SummaryCache):
    """Small process-local cache used to keep summary reads below latency targets."""

    def __init__(self, *, ttl_seconds: int = 120) -> None:
        self._ttl = timedelta(seconds=ttl_seconds)
        self._items: dict[str, SummaryCacheItem] = {}
        self._lock = Lock()

    def get(self, key: str) -> dict[str, object] | None:
        now = datetime.now(timezone.utc)
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            if item.expires_at < now:
                self._items.pop(key, None)
                return None
            return item.payload

    def set(self, key: str, payload: dict[str, object]) -> None:
        with self._lock:
            self._items[key] = SummaryCacheItem(
                payload=payload,
                expires_at=datetime.now(timezone.utc) + self._ttl,
            )

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
