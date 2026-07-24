"""Runtime state and metrics for synchronization orchestration."""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SyncMetrics:
    """Metrics for synchronization operations."""

    _values: dict[str, float] = field(
        default_factory=lambda: {
            "jobs_total": 0.0,
            "jobs_completed": 0.0,
            "jobs_failed": 0.0,
            "jobs_cancelled": 0.0,
            "records_total": 0.0,
            "records_imported": 0.0,
            "records_failed": 0.0,
            "pages_processed": 0.0,
            "checkpoints_created": 0.0,
            "checkpoints_restored": 0.0,
            "windows_processed": 0.0,
            "pipeline_executions": 0.0,
            "duration_total_seconds": 0.0,
            "duration_samples": 0.0,
        }
    )
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _per_domain: dict[str, dict[str, float]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(float)), repr=False)

    def inc(self, metric: str, value: float = 1.0, domain: str | None = None) -> None:
        """Increment a metric."""
        with self._lock:
            self._values[metric] = self._values.get(metric, 0.0) + value
            if domain:
                self._per_domain[domain][metric] += value

    def observe_duration(self, duration_seconds: float, domain: str | None = None) -> None:
        """Record job duration."""
        with self._lock:
            self._values["duration_total_seconds"] += duration_seconds
            self._values["duration_samples"] += 1.0
            if domain:
                self._per_domain[domain]["duration_total_seconds"] += duration_seconds
                self._per_domain[domain]["duration_samples"] += 1.0

    def snapshot(self) -> dict[str, Any]:
        """Get current metrics snapshot."""
        with self._lock:
            values = dict(self._values)
            per_domain = {
                domain: dict(metrics)
                for domain, metrics in self._per_domain.items()
            }

        # Calculate average duration
        samples = values.get("duration_samples", 0.0)
        total_duration = values.get("duration_total_seconds", 0.0)
        values["avg_duration_seconds"] = (total_duration / samples) if samples > 0 else 0.0

        # Calculate per-domain averages
        for domain_metrics in per_domain.values():
            domain_samples = domain_metrics.get("duration_samples", 0.0)
            domain_total = domain_metrics.get("duration_total_seconds", 0.0)
            domain_metrics["avg_duration_seconds"] = (domain_total / domain_samples) if domain_samples > 0 else 0.0

        return {
            "global": values,
            "per_domain": per_domain,
        }


@dataclass(slots=True)
class SyncRuntime:
    """Runtime state for synchronization orchestration."""

    metrics: SyncMetrics = field(default_factory=SyncMetrics, repr=False)
    _active_jobs: dict[str, float] = field(default_factory=dict, repr=False)  # job_id -> started_at
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _scheduler_running: bool = False
    _scheduler_last_run: float | None = None

    def register_job_started(self, job_id: str) -> None:
        """Register a job as started."""
        with self._lock:
            self._active_jobs[job_id] = time.monotonic()

    def register_job_completed(self, job_id: str, *, domain: str, records_imported: int, pages: int) -> None:
        """Register a job as completed."""
        with self._lock:
            started_at = self._active_jobs.pop(job_id, None)
            duration = (time.monotonic() - started_at) if started_at else 0.0

        self.metrics.inc("jobs_total", domain=domain)
        self.metrics.inc("jobs_completed", domain=domain)
        self.metrics.inc("records_total", value=float(records_imported), domain=domain)
        self.metrics.inc("records_imported", value=float(records_imported), domain=domain)
        self.metrics.inc("pages_processed", value=float(pages), domain=domain)
        if duration > 0:
            self.metrics.observe_duration(duration, domain=domain)

    def register_job_failed(self, job_id: str, *, domain: str) -> None:
        """Register a job as failed."""
        with self._lock:
            started_at = self._active_jobs.pop(job_id, None)
            duration = (time.monotonic() - started_at) if started_at else 0.0

        self.metrics.inc("jobs_total", domain=domain)
        self.metrics.inc("jobs_failed", domain=domain)
        if duration > 0:
            self.metrics.observe_duration(duration, domain=domain)

    def register_job_cancelled(self, job_id: str, *, domain: str) -> None:
        """Register a job as cancelled."""
        with self._lock:
            self._active_jobs.pop(job_id, None)

        self.metrics.inc("jobs_cancelled", domain=domain)

    def register_checkpoint_created(self, domain: str) -> None:
        """Register checkpoint creation."""
        self.metrics.inc("checkpoints_created", domain=domain)

    def register_checkpoint_restored(self, domain: str) -> None:
        """Register checkpoint restoration."""
        self.metrics.inc("checkpoints_restored", domain=domain)

    def register_window_processed(self, domain: str) -> None:
        """Register window processing."""
        self.metrics.inc("windows_processed", domain=domain)

    def register_pipeline_execution(self) -> None:
        """Register pipeline execution."""
        self.metrics.inc("pipeline_executions")

    def get_active_jobs_count(self) -> int:
        """Get count of currently active jobs."""
        with self._lock:
            return len(self._active_jobs)

    def mark_scheduler_running(self, running: bool) -> None:
        """Mark scheduler as running or stopped."""
        with self._lock:
            self._scheduler_running = running
            if running:
                self._scheduler_last_run = time.monotonic()

    def is_scheduler_running(self) -> bool:
        """Check if scheduler is running."""
        with self._lock:
            return self._scheduler_running

    def get_scheduler_last_run_seconds_ago(self) -> float | None:
        """Get seconds since scheduler last ran."""
        with self._lock:
            if self._scheduler_last_run is None:
                return None
            return time.monotonic() - self._scheduler_last_run

    def health_snapshot(self) -> dict[str, Any]:
        """Get health snapshot."""
        metrics_snapshot = self.metrics.snapshot()
        last_run_ago = self.get_scheduler_last_run_seconds_ago()

        return {
            "scheduler_running": self.is_scheduler_running(),
            "scheduler_last_run_seconds_ago": last_run_ago,
            "active_jobs": self.get_active_jobs_count(),
            "metrics": metrics_snapshot,
        }
