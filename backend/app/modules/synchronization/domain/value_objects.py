"""Value objects for synchronization domain."""
from __future__ import annotations

from enum import Enum


class JobStatus(str, Enum):
    """Status of a synchronization job."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    """Priority levels for synchronization jobs."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

    @property
    def weight(self) -> int:
        """Return numeric weight for priority comparison."""
        return {
            JobPriority.CRITICAL: 1000,
            JobPriority.HIGH: 100,
            JobPriority.NORMAL: 10,
            JobPriority.LOW: 1,
        }[self]


class SyncDomain(str, Enum):
    """Supported synchronization domains."""

    CUSTOMERS = "customers"
    PRODUCTS = "products"
    SALES = "sales"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    ACCOUNTS_PAYABLE = "accounts_payable"
    CASHFLOW = "cashflow"
    INVENTORY = "inventory"
    HR = "hr"
    SUPPLIERS = "suppliers"


class CheckpointStatus(str, Enum):
    """Status of a checkpoint."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    STALE = "stale"
