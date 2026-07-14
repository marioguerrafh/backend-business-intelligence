from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from hashlib import sha1
from typing import Any, Iterator

from app.modules.integrations.providers.omie.config import OmieProviderConfig


@dataclass(slots=True)
class TTLCache:
    _items: dict[str, tuple[float, dict[str, Any]]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            cached = self._items.get(key)
            if cached is None:
                return None
            expires_at, value = cached
            if expires_at <= time.monotonic():
                self._items.pop(key, None)
                return None
            return value

    def set(self, key: str, value: dict[str, Any], ttl_seconds: float) -> None:
        with self._lock:
            self._items[key] = (time.monotonic() + max(0.0, ttl_seconds), value)

    def size(self) -> int:
        with self._lock:
            return len(self._items)


@dataclass(slots=True)
class OmieMetrics:
    _values: dict[str, float] = field(
        default_factory=lambda: {
            "requests_total": 0.0,
            "requests_success": 0.0,
            "requests_failed": 0.0,
            "retry_total": 0.0,
            "cache_hits": 0.0,
            "cache_miss": 0.0,
            "pages_processed": 0.0,
            "records_imported": 0.0,
            "records_failed": 0.0,
            "rate_limit_waits": 0.0,
            "latency_total_ms": 0.0,
            "latency_samples": 0.0,
        }
    )
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def inc(self, name: str, value: float = 1.0) -> None:
        with self._lock:
            self._values[name] = self._values.get(name, 0.0) + value

    def observe_latency_ms(self, value_ms: float) -> None:
        with self._lock:
            self._values["latency_total_ms"] += max(0.0, value_ms)
            self._values["latency_samples"] += 1.0

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            values = dict(self._values)
        samples = values.get("latency_samples", 0.0)
        total = values.get("latency_total_ms", 0.0)
        values["avg_latency_ms"] = (total / samples) if samples > 0 else 0.0
        values.pop("latency_total_ms", None)
        values.pop("latency_samples", None)
        return values


@dataclass(slots=True)
class _WorkerState:
    in_flight: int = 0
    queue: deque[object] = field(default_factory=deque)
    condition: threading.Condition = field(default_factory=threading.Condition)


@dataclass(slots=True)
class WorkerPool:
    max_workers: int = 4
    _states: dict[str, _WorkerState] = field(default_factory=dict)
    _states_lock: threading.Lock = field(default_factory=threading.Lock)

    def _state_for(self, key: str) -> _WorkerState:
        with self._states_lock:
            if key not in self._states:
                self._states[key] = _WorkerState()
            return self._states[key]

    @contextmanager
    def slot(self, key: str) -> Iterator[None]:
        state = self._state_for(key)
        ticket = object()
        with state.condition:
            state.queue.append(ticket)
            while state.queue[0] is not ticket or state.in_flight >= self.max_workers:
                state.condition.wait()
            state.queue.popleft()
            state.in_flight += 1

        try:
            yield
        finally:
            with state.condition:
                state.in_flight = max(0, state.in_flight - 1)
                state.condition.notify_all()

    def snapshot(self) -> dict[str, int]:
        with self._states_lock:
            items = list(self._states.values())
        in_flight = sum(item.in_flight for item in items)
        queued = sum(len(item.queue) for item in items)
        return {"in_flight": in_flight, "queued": queued}


@dataclass(slots=True)
class OmieRateLimiter:
    max_requests_per_minute_ip: int
    max_requests_per_minute_method: int
    window_seconds: float = 60.0
    _ip_calls: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))
    _method_calls: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def _trim(self, calls: deque[float], now: float) -> None:
        threshold = now - self.window_seconds
        while calls and calls[0] <= threshold:
            calls.popleft()

    def acquire(self, *, ip: str, app_key: str, method: str) -> float:
        method_key = f"{ip}|{app_key}|{method}"

        total_wait = 0.0
        while True:
            with self._lock:
                now = time.monotonic()

                ip_calls = self._ip_calls[ip]
                method_calls = self._method_calls[method_key]

                self._trim(ip_calls, now)
                self._trim(method_calls, now)

                wait_ip = 0.0
                if len(ip_calls) >= self.max_requests_per_minute_ip and ip_calls:
                    wait_ip = max(0.0, ip_calls[0] + self.window_seconds - now)

                wait_method = 0.0
                if len(method_calls) >= self.max_requests_per_minute_method and method_calls:
                    wait_method = max(0.0, method_calls[0] + self.window_seconds - now)

                wait_for = max(wait_ip, wait_method)
                if wait_for <= 0.0:
                    stamp = time.monotonic()
                    ip_calls.append(stamp)
                    method_calls.append(stamp)
                    return total_wait

            time.sleep(wait_for)
            total_wait += wait_for


@dataclass(slots=True)
class OmieRuntime:
    config: OmieProviderConfig
    worker_pool: WorkerPool = field(init=False)
    rate_limiter: OmieRateLimiter = field(init=False)
    cache: TTLCache = field(init=False)
    metrics: OmieMetrics = field(init=False)
    _blocked_methods: dict[str, float] = field(default_factory=dict)
    _blocked_lock: threading.Lock = field(default_factory=threading.Lock)
    _last_rate_limit_remaining: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.worker_pool = WorkerPool(max_workers=max(1, self.config.max_parallel_requests))
        self.rate_limiter = OmieRateLimiter(
            max_requests_per_minute_ip=max(1, self.config.max_requests_per_minute_ip),
            max_requests_per_minute_method=max(1, self.config.max_requests_per_method),
        )
        self.cache = TTLCache()
        self.metrics = OmieMetrics()

    @staticmethod
    def method_key(*, ip: str, app_key: str, method: str) -> str:
        return f"{ip}|{app_key}|{method}"

    @staticmethod
    def cache_key(*, url: str, payload: dict[str, Any]) -> str:
        text = json.dumps({"url": url, "payload": payload}, sort_keys=True, ensure_ascii=True, default=str)
        return sha1(text.encode("utf-8")).hexdigest()

    def block_method(self, *, method_key: str, seconds: float) -> None:
        unblock_at = time.monotonic() + max(0.0, seconds)
        with self._blocked_lock:
            current = self._blocked_methods.get(method_key)
            if current is None or current < unblock_at:
                self._blocked_methods[method_key] = unblock_at

    def wait_if_method_blocked(self, *, method_key: str) -> float:
        total_wait = 0.0
        while True:
            with self._blocked_lock:
                blocked_until = self._blocked_methods.get(method_key)
                if blocked_until is None:
                    return total_wait
                now = time.monotonic()
                remaining = blocked_until - now
                if remaining <= 0:
                    self._blocked_methods.pop(method_key, None)
                    return total_wait
            time.sleep(remaining)
            total_wait += remaining

    def set_rate_limit_remaining(self, *, method_key: str, remaining: str) -> None:
        with self._blocked_lock:
            self._last_rate_limit_remaining[method_key] = remaining

    def get_rate_limit_remaining(self, *, method_key: str) -> str | None:
        with self._blocked_lock:
            return self._last_rate_limit_remaining.get(method_key)

    def health_snapshot(self) -> dict[str, Any]:
        queue = self.worker_pool.snapshot()
        return {
            "metrics": self.metrics.snapshot(),
            "queue": queue,
            "cache_size": self.cache.size(),
        }
