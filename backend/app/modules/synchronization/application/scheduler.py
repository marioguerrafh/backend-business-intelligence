"""Intelligent scheduler for automatic synchronization."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.modules.synchronization.application.orchestrator import SynchronizationOrchestrator
from app.modules.synchronization.domain.value_objects import JobPriority, SyncDomain


@dataclass(slots=True)
class DomainScheduleConfig:
    """Configuration for domain sync scheduling."""

    domain: SyncDomain
    frequency_minutes: int
    window_days: int
    priority: JobPriority = JobPriority.NORMAL
    enabled: bool = True
    max_parallel_jobs: int = 1

    def next_run_at(self, last_run: datetime) -> datetime:
        """Calculate next run time."""
        return last_run + timedelta(minutes=self.frequency_minutes)


@dataclass(slots=True)
class SchedulerState:
    """State tracking for scheduler."""

    last_runs: dict[str, datetime] = field(default_factory=dict)  # domain -> last_run
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def update_last_run(self, domain: str, timestamp: datetime) -> None:
        """Update last run time for a domain."""
        with self._lock:
            self.last_runs[domain] = timestamp

    def get_last_run(self, domain: str) -> datetime | None:
        """Get last run time for a domain."""
        with self._lock:
            return self.last_runs.get(domain)


@dataclass(slots=True)
class SynchronizationScheduler:
    """Intelligent scheduler for automatic synchronization."""

    orchestrator: SynchronizationOrchestrator
    schedule_configs: dict[str, DomainScheduleConfig]  # domain -> config
    state: SchedulerState = field(default_factory=SchedulerState)
    _running: bool = field(default=False, init=False)
    _thread: threading.Thread | None = field(default=None, init=False, repr=False)
    _shutdown_event: threading.Event = field(default_factory=threading.Event, init=False, repr=False)
    _logger: logging.Logger = logging.getLogger("app.synchronization.scheduler")

    @classmethod
    def from_config(
        cls,
        orchestrator: SynchronizationOrchestrator,
        config: dict[str, Any],
    ) -> SynchronizationScheduler:
        """Create scheduler from configuration dictionary."""
        schedule_configs = {}

        for domain_name, domain_config in config.items():
            try:
                domain = SyncDomain(domain_name)
            except ValueError:
                continue  # Skip invalid domain names

            schedule_configs[domain_name] = DomainScheduleConfig(
                domain=domain,
                frequency_minutes=cls._parse_frequency(domain_config.get("frequency", "60m")),
                window_days=domain_config.get("window_days", 30),
                priority=JobPriority(domain_config.get("priority", "normal")),
                enabled=domain_config.get("enabled", True),
                max_parallel_jobs=domain_config.get("max_parallel_jobs", 1),
            )

        return cls(orchestrator=orchestrator, schedule_configs=schedule_configs)

    @staticmethod
    def _parse_frequency(frequency_str: str) -> int:
        """Parse frequency string to minutes."""
        freq = frequency_str.lower().strip()

        if freq == "daily":
            return 24 * 60
        if freq == "hourly":
            return 60

        # Parse format like "15m", "30m", "2h"
        if freq.endswith("m"):
            return int(freq[:-1])
        if freq.endswith("h"):
            return int(freq[:-1]) * 60

        # Default to 60 minutes
        return 60

    def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return

        self._running = True
        self._shutdown_event.clear()
        self._thread = threading.Thread(
            target=self._scheduler_loop,
            name="sync-scheduler",
            daemon=True,
        )
        self._thread.start()
        self.orchestrator.runtime.mark_scheduler_running(True)

        self._logger.info("Synchronization scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

        self.orchestrator.runtime.mark_scheduler_running(False)
        self._logger.info("Synchronization scheduler stopped")

    def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._running and not self._shutdown_event.is_set():
            try:
                self._check_and_schedule_due_syncs()
            except Exception as exc:
                self._logger.error(f"Scheduler error: {exc}", exc_info=True)

            # Sleep for 30 seconds before next check
            self._shutdown_event.wait(timeout=30)

    def _check_and_schedule_due_syncs(self) -> None:
        """Check which syncs are due and schedule them."""
        now = datetime.utcnow()

        for domain_name, config in self.schedule_configs.items():
            if not config.enabled:
                continue

            last_run = self.state.get_last_run(domain_name)

            # If never run, schedule immediately
            if last_run is None:
                self._schedule_domain_sync(config, now)
                continue

            # Check if due for next run
            next_run = config.next_run_at(last_run)
            if now >= next_run:
                self._schedule_domain_sync(config, now)

    def _schedule_domain_sync(self, config: DomainScheduleConfig, timestamp: datetime) -> None:
        """Schedule a sync for a specific domain."""
        try:
            # Note: This is a simplified version. In production, you would:
            # 1. Get connection details from integration repository
            # 2. Get encrypted credentials
            # 3. Schedule through orchestrator

            self._logger.info(
                f"Would schedule {config.domain.value} sync (frequency: {config.frequency_minutes}m)",
                extra={
                    "domain": config.domain.value,
                    "frequency_minutes": config.frequency_minutes,
                    "window_days": config.window_days,
                    "priority": config.priority.value,
                },
            )

            # Update last run
            self.state.update_last_run(config.domain.value, timestamp)

        except Exception as exc:
            self._logger.error(
                f"Failed to schedule {config.domain.value} sync: {exc}",
                exc_info=True,
            )

    def get_schedule_status(self) -> dict[str, Any]:
        """Get current schedule status."""
        now = datetime.utcnow()
        statuses = {}

        for domain_name, config in self.schedule_configs.items():
            last_run = self.state.get_last_run(domain_name)
            next_run = config.next_run_at(last_run) if last_run else now

            statuses[domain_name] = {
                "enabled": config.enabled,
                "frequency_minutes": config.frequency_minutes,
                "window_days": config.window_days,
                "priority": config.priority.value,
                "last_run": last_run.isoformat() if last_run else None,
                "next_run": next_run.isoformat(),
                "seconds_until_next": (next_run - now).total_seconds() if next_run > now else 0,
            }

        return {
            "running": self._running,
            "schedules": statuses,
        }

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running
