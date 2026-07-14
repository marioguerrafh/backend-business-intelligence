from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True, frozen=True)
class ProviderAuthResult:
    connected: bool
    external_account_id: str | None = None


@dataclass(slots=True, frozen=True)
class TemplateSyncResult:
    template: str
    records_read: int
    records_imported: int
    records_failed: int
    import_job_id: str | None
    ingest_event_id: str | None
    pipeline_run_id: str | None = None


@dataclass(slots=True, frozen=True)
class ProviderSyncResult:
    provider: str
    records_read: int
    records_imported: int
    records_failed: int
    template_results: tuple[TemplateSyncResult, ...]


class ERPProvider(Protocol):
    provider_type: str

    def authenticate(self, *, company_id: str, credentials: dict[str, Any]) -> ProviderAuthResult: ...

    def health(self, *, company_id: str, credentials: dict[str, Any]) -> dict[str, Any]: ...

    def sync_customers(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult: ...

    def sync_products(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult: ...

    def sync_suppliers(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult: ...

    def sync_sales(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult: ...

    def sync_accounts_receivable(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult: ...

    def sync_accounts_payable(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult: ...

    def sync_cashflow(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult: ...

    def sync_inventory(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult: ...

    def sync_hr(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult: ...

    def full_sync(self, *, company_id: str, credentials: dict[str, Any]) -> ProviderSyncResult: ...

    def incremental_sync(self, *, company_id: str, credentials: dict[str, Any]) -> ProviderSyncResult: ...

    def disconnect(self, *, company_id: str, credentials: dict[str, Any]) -> None: ...
