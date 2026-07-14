from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.modules.integrations.application.provider_interface import (
    ProviderAuthResult,
    ProviderSyncResult,
    TemplateSyncResult,
)


@dataclass(slots=True)
class StubERPProvider:
    provider_type: str

    def authenticate(self, *, company_id: str, credentials: dict[str, Any]) -> ProviderAuthResult:
        if not credentials:
            raise ValueError("credentials are required")
        return ProviderAuthResult(connected=True, external_account_id=f"{self.provider_type}:{company_id}")

    def health(self, *, company_id: str, credentials: dict[str, Any]) -> dict[str, Any]:
        self.authenticate(company_id=company_id, credentials=credentials)
        return {"provider": self.provider_type, "status": "ok"}

    def sync_customers(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        return self._empty("customers")

    def sync_products(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        return self._empty("products")

    def sync_suppliers(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        return self._empty("suppliers")

    def sync_sales(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        return self._empty("sales")

    def sync_accounts_receivable(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        return self._empty("accounts_receivable")

    def sync_accounts_payable(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        return self._empty("accounts_payable")

    def sync_cashflow(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        return self._empty("cashflow")

    def sync_inventory(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        return self._empty("inventory")

    def sync_hr(self, *, company_id: str, credentials: dict[str, Any], mode: str) -> TemplateSyncResult:
        return self._empty("hr")

    def full_sync(self, *, company_id: str, credentials: dict[str, Any]) -> ProviderSyncResult:
        return ProviderSyncResult(
            provider=self.provider_type,
            records_read=0,
            records_imported=0,
            records_failed=0,
            template_results=(),
        )

    def incremental_sync(self, *, company_id: str, credentials: dict[str, Any]) -> ProviderSyncResult:
        return self.full_sync(company_id=company_id, credentials=credentials)

    def disconnect(self, *, company_id: str, credentials: dict[str, Any]) -> None:
        return None

    @staticmethod
    def _empty(template: str) -> TemplateSyncResult:
        return TemplateSyncResult(
            template=template,
            records_read=0,
            records_imported=0,
            records_failed=0,
            import_job_id=None,
            ingest_event_id=None,
        )
