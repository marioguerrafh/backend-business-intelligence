from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Literal, TypeVar

T = TypeVar("T")


class RetryableProviderError(ValueError):
    def __init__(self, message: str, *, retry_after_seconds: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.15
    backoff_strategy: Literal["linear", "exponential"] = "linear"
    max_delay_seconds: float | None = None


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
    _state: Literal["closed", "open", "half_open"] = "closed"
    _consecutive_failures: int = 0
    _opened_at: float | None = None

    def before_call(self) -> None:
        if self._state == "closed":
            return
        if self._state == "open" and self._opened_at is not None:
            elapsed = time.monotonic() - self._opened_at
            if elapsed >= self.recovery_timeout_seconds:
                self._state = "half_open"
                self._opened_at = None
                return
            raise ValueError("provider circuit breaker is open")
        if self._state == "half_open":
            return

    def on_success(self) -> None:
        self._consecutive_failures = 0
        self._state = "closed"
        self._opened_at = None

    def on_failure(self) -> None:
        if self._state == "half_open":
            self._state = "open"
            self._opened_at = time.monotonic()
            self._consecutive_failures = self.failure_threshold
            return

        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._state = "open"
            self._opened_at = time.monotonic()

    def snapshot(self) -> dict[str, float | int | str | None]:
        return {
            "state": self._state,
            "failure_threshold": self.failure_threshold,
            "consecutive_failures": self._consecutive_failures,
            "recovery_timeout_seconds": self.recovery_timeout_seconds,
            "opened_at_monotonic": self._opened_at,
        }


def _compute_backoff_delay(*, retry: RetryPolicy, attempt: int) -> float:
    if retry.backoff_strategy == "exponential":
        delay = retry.base_delay_seconds * (2 ** max(0, attempt - 1))
    else:
        delay = retry.base_delay_seconds * attempt

    if retry.max_delay_seconds is not None:
        return min(delay, retry.max_delay_seconds)
    return delay


def resilient_call(
    *,
    fn: Callable[[], T],
    retry: RetryPolicy,
    rate_limiter: RateLimiter | None,
    circuit_breaker: CircuitBreaker,
    on_retry: Callable[[int, Exception, float], None] | None = None,
) -> T:
    circuit_breaker.before_call()

    attempt = 0
    last_exc: Exception | None = None
    while attempt < retry.max_attempts:
        attempt += 1
        if rate_limiter is not None:
            rate_limiter.acquire()
        try:
            result = fn()
            circuit_breaker.on_success()
            return result
        except Exception as exc:
            if not isinstance(exc, RetryableProviderError):
                circuit_breaker.on_failure()
                raise

            circuit_breaker.on_failure()
            last_exc = exc
            if attempt >= retry.max_attempts:
                break
            delay_seconds = _compute_backoff_delay(retry=retry, attempt=attempt)
            if exc.retry_after_seconds is not None:
                delay_seconds = max(delay_seconds, float(exc.retry_after_seconds))
            if on_retry is not None:
                on_retry(attempt, exc, delay_seconds)
            time.sleep(delay_seconds)

    if last_exc is not None:
        raise last_exc
    raise ValueError("unexpected resilient call state")
