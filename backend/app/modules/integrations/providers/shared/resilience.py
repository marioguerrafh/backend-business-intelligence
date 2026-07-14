from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.15


@dataclass(slots=True)
class RateLimiter:
    max_requests_per_second: int
    _calls: deque[float] = field(default_factory=deque)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            window_start = now - 1.0
            while self._calls and self._calls[0] < window_start:
                self._calls.popleft()
            if len(self._calls) >= self.max_requests_per_second:
                sleep_seconds = max(0.0, self._calls[0] + 1.0 - now)
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
            self._calls.append(time.monotonic())


@dataclass(slots=True)
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout_seconds: float = 20.0
    _failures: int = 0
    _opened_at: float | None = None

    def before_call(self) -> None:
        if self._opened_at is None:
            return
        elapsed = time.monotonic() - self._opened_at
        if elapsed >= self.recovery_timeout_seconds:
            self._opened_at = None
            self._failures = 0
            return
        raise ValueError("provider circuit breaker is open")

    def on_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def on_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._opened_at = time.monotonic()


def resilient_call(
    *,
    fn: Callable[[], T],
    retry: RetryPolicy,
    rate_limiter: RateLimiter,
    circuit_breaker: CircuitBreaker,
) -> T:
    circuit_breaker.before_call()

    attempt = 0
    last_exc: Exception | None = None
    while attempt < retry.max_attempts:
        attempt += 1
        rate_limiter.acquire()
        try:
            result = fn()
            circuit_breaker.on_success()
            return result
        except Exception as exc:
            circuit_breaker.on_failure()
            last_exc = exc
            if attempt >= retry.max_attempts:
                break
            time.sleep(retry.base_delay_seconds * attempt)

    if last_exc is not None:
        raise last_exc
    raise ValueError("unexpected resilient call state")
