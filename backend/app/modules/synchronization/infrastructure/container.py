"""Dependency injection container for synchronization module."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.integrations.application.provider_registry import ProviderRegistry
from app.modules.integrations.infrastructure.container import build_integrations_container
from app.modules.integrations.infrastructure.security import CredentialCipher
from app.modules.synchronization.application.job_dispatcher import JobDispatcher
from app.modules.synchronization.application.orchestrator import SynchronizationOrchestrator
from app.modules.synchronization.application.scheduler import SynchronizationScheduler
from app.modules.synchronization.infrastructure.repositories import CheckpointRepository, JobRepository
from app.modules.synchronization.infrastructure.sync_runtime import SyncRuntime
from app.modules.synchronization.infrastructure.window_manager import WindowManager
from app.modules.synchronization.infrastructure.worker_pool import WorkerPool

# Global singleton instances
_ORCHESTRATOR: SynchronizationOrchestrator | None = None
_SCHEDULER: SynchronizationScheduler | None = None
_WORKER_POOL: WorkerPool | None = None
_RUNTIME: SyncRuntime | None = None


def load_synchronization_config() -> dict[str, Any]:
    """Load synchronization configuration from YAML file."""
    config_path = Path("synchronization.yaml")
    if not config_path.exists():
        # Return default configuration
        return {
            "customers": {
                "frequency": "daily",
                "window_days": 3650,
                "priority": "low",
                "enabled": True,
                "max_parallel_jobs": 1,
            },
            "products": {
                "frequency": "daily",
                "window_days": 3650,
                "priority": "low",
                "enabled": True,
                "max_parallel_jobs": 1,
            },
            "sales": {
                "frequency": "15m",
                "window_days": 7,
                "priority": "high",
                "enabled": True,
                "max_parallel_jobs": 1,
            },
            "accounts_receivable": {
                "frequency": "30m",
                "window_days": 30,
                "priority": "normal",
                "enabled": True,
                "max_parallel_jobs": 1,
            },
            "accounts_payable": {
                "frequency": "30m",
                "window_days": 30,
                "priority": "normal",
                "enabled": True,
                "max_parallel_jobs": 1,
            },
            "cashflow": {
                "frequency": "10m",
                "window_days": 30,
                "priority": "high",
                "enabled": True,
                "max_parallel_jobs": 1,
            },
            "inventory": {
                "frequency": "60m",
                "window_days": 30,
                "priority": "normal",
                "enabled": True,
                "max_parallel_jobs": 1,
            },
            "hr": {
                "frequency": "daily",
                "window_days": 30,
                "priority": "low",
                "enabled": True,
                "max_parallel_jobs": 1,
            },
        }

    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}


def get_sync_runtime() -> SyncRuntime:
    """Get or create singleton sync runtime."""
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = SyncRuntime()
    return _RUNTIME


def get_worker_pool() -> WorkerPool:
    """Get or create singleton worker pool."""
    global _WORKER_POOL
    if _WORKER_POOL is None:
        max_workers = int(os.getenv("SYNC_MAX_WORKERS", "4"))
        _WORKER_POOL = WorkerPool(max_workers=max_workers)
        _WORKER_POOL.start()
    return _WORKER_POOL


def build_orchestrator(session: Session) -> SynchronizationOrchestrator:
    """Build synchronization orchestrator with all dependencies."""
    # Get repositories
    job_repository = JobRepository(session=session)
    checkpoint_repository = CheckpointRepository(session=session)

    # Get runtime components
    runtime = get_sync_runtime()
    worker_pool = get_worker_pool()
    window_manager = WindowManager()

    # Get integration components
    integrations_container = build_integrations_container(session)
    provider_registry = integrations_container.service.provider_registry
    credential_cipher = integrations_container.service.credential_cipher

    # Build dispatcher
    job_dispatcher = JobDispatcher(
        job_repository=job_repository,
        checkpoint_repository=checkpoint_repository,
        provider_registry=provider_registry,
        credential_cipher=credential_cipher,
        runtime=runtime,
    )

    # Build orchestrator
    orchestrator = SynchronizationOrchestrator(
        job_repository=job_repository,
        checkpoint_repository=checkpoint_repository,
        job_dispatcher=job_dispatcher,
        window_manager=window_manager,
        worker_pool=worker_pool,
        runtime=runtime,
    )

    return orchestrator


def get_orchestrator() -> SynchronizationOrchestrator:
    """Get orchestrator instance (FastAPI dependency)."""
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        session = next(get_db())
        _ORCHESTRATOR = build_orchestrator(session)
        _ORCHESTRATOR.start()
    return _ORCHESTRATOR


def get_scheduler() -> SynchronizationScheduler:
    """Get scheduler instance (FastAPI dependency)."""
    global _SCHEDULER
    if _SCHEDULER is None:
        orchestrator = get_orchestrator()
        config = load_synchronization_config()
        _SCHEDULER = SynchronizationScheduler.from_config(
            orchestrator=orchestrator,
            config=config,
        )
    return _SCHEDULER


def shutdown_synchronization() -> None:
    """Shutdown synchronization components gracefully."""
    global _SCHEDULER, _ORCHESTRATOR, _WORKER_POOL, _RUNTIME

    if _SCHEDULER:
        _SCHEDULER.stop()
        _SCHEDULER = None

    if _ORCHESTRATOR:
        _ORCHESTRATOR.shutdown()
        _ORCHESTRATOR = None

    if _WORKER_POOL:
        _WORKER_POOL.shutdown(wait=True)
        _WORKER_POOL = None

    _RUNTIME = None
