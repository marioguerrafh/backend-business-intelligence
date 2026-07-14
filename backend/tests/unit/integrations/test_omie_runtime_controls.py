from __future__ import annotations

import threading
import time

from app.modules.integrations.providers.omie.config import OmieProviderConfig
from app.modules.integrations.providers.omie.runtime import OmieRateLimiter, TTLCache, WorkerPool
from app.modules.integrations.providers.shared.resilience import CircuitBreaker, RetryPolicy, _compute_backoff_delay


def test_cache_ttl_expires() -> None:
    cache = TTLCache()
    cache.set("k", {"v": 1}, ttl_seconds=0.02)
    assert cache.get("k") == {"v": 1}
    time.sleep(0.03)
    assert cache.get("k") is None


def test_worker_pool_fifo_single_worker() -> None:
    pool = WorkerPool(max_workers=1)
    order: list[int] = []

    def run(i: int) -> None:
        with pool.slot("key"):
            order.append(i)
            time.sleep(0.01)

    threads = [threading.Thread(target=run, args=(idx,)) for idx in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert order == [0, 1, 2, 3, 4]


def test_rate_limiter_respects_method_window() -> None:
    limiter = OmieRateLimiter(
        max_requests_per_minute_ip=100,
        max_requests_per_minute_method=1,
        window_seconds=0.05,
    )

    waited_first = limiter.acquire(ip="ip", app_key="key", method="ListarClientes")
    waited_second = limiter.acquire(ip="ip", app_key="key", method="ListarClientes")

    assert waited_first >= 0.0
    assert waited_second > 0.0


def test_circuit_breaker_half_open_recovery() -> None:
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=0.02)

    breaker.on_failure()
    breaker.on_failure()
    snapshot_open = breaker.snapshot()
    assert snapshot_open["state"] == "open"

    time.sleep(0.03)
    breaker.before_call()
    snapshot_half = breaker.snapshot()
    assert snapshot_half["state"] == "half_open"

    breaker.on_success()
    snapshot_closed = breaker.snapshot()
    assert snapshot_closed["state"] == "closed"


def test_exponential_backoff_delay() -> None:
    retry = RetryPolicy(max_attempts=5, base_delay_seconds=1.0, backoff_strategy="exponential", max_delay_seconds=8.0)
    assert _compute_backoff_delay(retry=retry, attempt=1) == 1.0
    assert _compute_backoff_delay(retry=retry, attempt=2) == 2.0
    assert _compute_backoff_delay(retry=retry, attempt=3) == 4.0
    assert _compute_backoff_delay(retry=retry, attempt=4) == 8.0
    assert _compute_backoff_delay(retry=retry, attempt=5) == 8.0


def test_config_defaults_match_official_limits() -> None:
    cfg = OmieProviderConfig()
    assert cfg.max_requests_per_minute_ip == 960
    assert cfg.max_requests_per_method == 240
    assert cfg.max_parallel_requests == 4
