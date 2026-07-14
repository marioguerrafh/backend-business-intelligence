from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Protocol

from app.modules.business.application.contracts import UpsertCustomerCommand
from app.modules.business.application.product_contracts import UpsertProductCommand
from app.modules.business.domain.product_value_objects import ProductExternalReference, ProductStatus, normalize_sku
from app.modules.business.domain.value_objects import (
    ContactChannel,
    ContactChannelType,
    CustomerStatus,
    ExternalReference,
    normalize_document_number,
)
from app.modules.imports.infrastructure.repositories import ImportRepository


class PipelineCoordinatorPort(Protocol):
    def consume_ingest_completed(
        self,
        *,
        company_id: str,
        import_job_id: str,
        template: str,
        source_system: str,
        event_id: str | None,
        correlation_id: str | None,
    ): ...


class UpsertCustomerPort(Protocol):
    def execute(self, command: UpsertCustomerCommand): ...


class UpsertProductPort(Protocol):
    def execute(self, command: UpsertProductCommand): ...


@dataclass(slots=True, frozen=True)
class TemplateIngestResult:
    template: str
    records_read: int
    records_imported: int
    records_failed: int
    import_job_id: str
    ingest_event_id: str | None
    pipeline_run_id: str | None


@dataclass(slots=True)
class IntegrationIngestGateway:
    import_repository: ImportRepository
    upsert_customer: UpsertCustomerPort
    upsert_product: UpsertProductPort
    pipeline_coordinator: PipelineCoordinatorPort | None

    def ingest_customers(
        self,
        *,
        company_id: str,
        source_system: str,
        records: list[dict[str, Any]],
        correlation_id: str | None,
    ) -> TemplateIngestResult:
        job_id = self.import_repository.create_job(
            company_id=company_id,
            template="customers",
            source_system=source_system,
            canonical_schema_version="2.0.0",
            correlation_id=correlation_id,
        )
        imported = 0
        failed = 0
        seen_source_record_ids: set[str] = set()
        seen_documents: set[str] = set()
        seen_external_ids: set[str] = set()
        for item in records:
            try:
                external_id = str(item.get("external_id") or "").strip()
                source_record_id = str(item.get("source_record_id") or external_id or "unknown").strip() or "unknown"
                raw_document = str(item.get("document") or "").strip() or None
                normalized_document = normalize_document_number(raw_document)

                # Session autoflush is disabled for performance. Deduplicate within the same batch
                # to avoid pending duplicate inserts that would fail only at finish_job flush time.
                if source_record_id in seen_source_record_ids:
                    continue
                if external_id and external_id in seen_external_ids:
                    continue
                if normalized_document and normalized_document in seen_documents:
                    continue

                contacts: list[ContactChannel] = []
                email = str(item.get("email") or "").strip()
                phone = str(item.get("phone") or "").strip()
                if email:
                    contacts.append(ContactChannel(channel_type=ContactChannelType.EMAIL, value=email))
                if phone:
                    contacts.append(ContactChannel(channel_type=ContactChannelType.PHONE, value=phone))

                refs = (
                    ExternalReference(source_system=source_system, external_id=(external_id or source_record_id)),
                )
                self.upsert_customer.execute(
                    UpsertCustomerCommand(
                        company_id=company_id,
                        legal_name=str(item.get("legal_name") or item.get("name") or "Cliente ERP"),
                        trade_name=str(item.get("trade_name") or item.get("name") or "Cliente ERP"),
                        document_number=raw_document,
                        status=CustomerStatus(str(item.get("status") or "active").lower()),
                        billing_address=None,
                        contacts=tuple(contacts),
                        external_refs=refs,
                        source_system=source_system,
                        source_record_id=source_record_id,
                        canonical_schema_version="2.0.0",
                        correlation_id=correlation_id,
                    )
                )
                seen_source_record_ids.add(source_record_id)
                if external_id:
                    seen_external_ids.add(external_id)
                if normalized_document:
                    seen_documents.add(normalized_document)
                imported += 1
            except Exception:
                failed += 1

        return self._finish_and_trigger(
            company_id=company_id,
            source_system=source_system,
            template="customers",
            job_id=job_id,
            records_read=len(records),
            records_imported=imported,
            records_failed=failed,
            correlation_id=correlation_id,
        )

    def ingest_products(
        self,
        *,
        company_id: str,
        source_system: str,
        records: list[dict[str, Any]],
        correlation_id: str | None,
    ) -> TemplateIngestResult:
        job_id = self.import_repository.create_job(
            company_id=company_id,
            template="products",
            source_system=source_system,
            canonical_schema_version="2.0.0",
            correlation_id=correlation_id,
        )
        imported = 0
        failed = 0
        seen_source_record_ids: set[str] = set()
        seen_external_ids: set[str] = set()
        seen_skus: set[str] = set()
        for item in records:
            try:
                external_id = str(item.get("external_id") or "").strip()
                sku_value = str(item.get("sku") or external_id or "sku-unknown")
                source_record_id = str(item.get("source_record_id") or external_id or sku_value).strip() or "sku-unknown"

                normalized_sku: str | None = None
                try:
                    normalized_sku = normalize_sku(sku_value)
                except ValueError:
                    normalized_sku = None

                if source_record_id in seen_source_record_ids:
                    continue
                if external_id and external_id in seen_external_ids:
                    continue
                if normalized_sku and normalized_sku in seen_skus:
                    continue

                refs = (
                    ProductExternalReference(
                        source_system=source_system,
                        external_id=(external_id or source_record_id),
                    ),
                )
                self.upsert_product.execute(
                    UpsertProductCommand(
                        company_id=company_id,
                        sku=sku_value,
                        name=str(item.get("name") or "Produto ERP"),
                        category=(str(item.get("category") or "").strip() or None),
                        unit_of_measure=str(item.get("unit") or "UN"),
                        status=ProductStatus(str(item.get("status") or "active").lower()),
                        default_cost=Decimal(str(item.get("default_cost") or "0")),
                        default_price=Decimal(str(item.get("default_price") or "0")),
                        tax_profile_ref=(str(item.get("tax_profile_ref") or "").strip() or None),
                        external_refs=refs,
                        source_system=source_system,
                        source_record_id=source_record_id,
                        canonical_schema_version="2.0.0",
                        correlation_id=correlation_id,
                    )
                )
                seen_source_record_ids.add(source_record_id)
                if external_id:
                    seen_external_ids.add(external_id)
                if normalized_sku:
                    seen_skus.add(normalized_sku)
                imported += 1
            except Exception:
                failed += 1

        return self._finish_and_trigger(
            company_id=company_id,
            source_system=source_system,
            template="products",
            job_id=job_id,
            records_read=len(records),
            records_imported=imported,
            records_failed=failed,
            correlation_id=correlation_id,
        )

    def ingest_sales(
        self,
        *,
        company_id: str,
        source_system: str,
        records: list[dict[str, Any]],
        correlation_id: str | None,
    ) -> TemplateIngestResult:
        job_id = self.import_repository.create_job(
            company_id=company_id,
            template="sales",
            source_system=source_system,
            canonical_schema_version="2.0.0",
            correlation_id=correlation_id,
        )
        imported = 0
        failed = 0
        seen_source_record_ids: set[str] = set()
        for item in records:
            try:
                source_record_id = str(item["source_record_id"])
                if source_record_id in seen_source_record_ids:
                    continue

                ok = self.import_repository.persist_sale_fact(
                    job_id=job_id,
                    company_id=company_id,
                    source_system=source_system,
                    source_record_id=source_record_id,
                    period_ref=str(item["period_ref"]),
                    transaction_date=item["transaction_date"],
                    invoice_id=str(item["invoice_id"]),
                    invoice_line_id=str(item.get("invoice_line_id") or "1"),
                    product_external_id=str(item["product_external_id"]),
                    customer_external_id=str(item["customer_external_id"]),
                    gross_revenue=float(item["gross_revenue"]),
                    tax_amount=float(item["tax_amount"]),
                    discount_amount=float(item["discount_amount"]),
                    return_amount=float(item["return_amount"]),
                    net_revenue=float(item["net_revenue"]),
                    quantity_sold=float(item["quantity_sold"]),
                    cogs_amount=float(item["cogs_amount"]),
                )
                if ok:
                    seen_source_record_ids.add(source_record_id)
                    imported += 1
            except Exception:
                failed += 1

        return self._finish_and_trigger(
            company_id=company_id,
            source_system=source_system,
            template="sales",
            job_id=job_id,
            records_read=len(records),
            records_imported=imported,
            records_failed=failed,
            correlation_id=correlation_id,
        )

    def ingest_accounts_receivable(
        self,
        *,
        company_id: str,
        source_system: str,
        records: list[dict[str, Any]],
        correlation_id: str | None,
    ) -> TemplateIngestResult:
        return self._ingest_financial_template(
            template="accounts_receivable",
            company_id=company_id,
            source_system=source_system,
            records=records,
            correlation_id=correlation_id,
        )

    def ingest_accounts_payable(
        self,
        *,
        company_id: str,
        source_system: str,
        records: list[dict[str, Any]],
        correlation_id: str | None,
    ) -> TemplateIngestResult:
        return self._ingest_financial_template(
            template="accounts_payable",
            company_id=company_id,
            source_system=source_system,
            records=records,
            correlation_id=correlation_id,
        )

    def ingest_cashflow(
        self,
        *,
        company_id: str,
        source_system: str,
        records: list[dict[str, Any]],
        correlation_id: str | None,
    ) -> TemplateIngestResult:
        return self._ingest_financial_template(
            template="cashflow",
            company_id=company_id,
            source_system=source_system,
            records=records,
            correlation_id=correlation_id,
        )

    def ingest_inventory(
        self,
        *,
        company_id: str,
        source_system: str,
        records: list[dict[str, Any]],
        correlation_id: str | None,
    ) -> TemplateIngestResult:
        return self._ingest_financial_template(
            template="inventory",
            company_id=company_id,
            source_system=source_system,
            records=records,
            correlation_id=correlation_id,
        )

    def ingest_hr(
        self,
        *,
        company_id: str,
        source_system: str,
        records: list[dict[str, Any]],
        correlation_id: str | None,
    ) -> TemplateIngestResult:
        return self._ingest_financial_template(
            template="hr",
            company_id=company_id,
            source_system=source_system,
            records=records,
            correlation_id=correlation_id,
        )

    def _ingest_financial_template(
        self,
        *,
        template: str,
        company_id: str,
        source_system: str,
        records: list[dict[str, Any]],
        correlation_id: str | None,
    ) -> TemplateIngestResult:
        job_id = self.import_repository.create_job(
            company_id=company_id,
            template=template,
            source_system=source_system,
            canonical_schema_version="2.0.0",
            correlation_id=correlation_id,
        )
        imported = 0
        failed = 0
        seen_source_record_ids: set[str] = set()

        for item in records:
            try:
                source_record_id = str(item["source_record_id"])
                if source_record_id in seen_source_record_ids:
                    continue

                if template == "accounts_receivable":
                    ok = self.import_repository.persist_accounts_receivable_fact(
                        job_id=job_id,
                        company_id=company_id,
                        source_system=source_system,
                        source_record_id=source_record_id,
                        period_ref=str(item["period_ref"]),
                        customer_id=str(item["customer_id"]),
                        invoice_number=str(item["invoice_number"]),
                        issue_date=item["issue_date"],
                        due_date=item["due_date"],
                        payment_date=item.get("payment_date"),
                        amount=float(item["amount"]),
                        received_amount=float(item["received_amount"]),
                        outstanding_amount=float(item["outstanding_amount"]),
                        status=str(item["status"]),
                        aging_days=int(item["aging_days"]),
                    )
                elif template == "accounts_payable":
                    ok = self.import_repository.persist_accounts_payable_fact(
                        job_id=job_id,
                        company_id=company_id,
                        source_system=source_system,
                        source_record_id=source_record_id,
                        period_ref=str(item["period_ref"]),
                        supplier_id=str(item["supplier_id"]),
                        invoice_number=str(item["invoice_number"]),
                        issue_date=item["issue_date"],
                        due_date=item["due_date"],
                        payment_date=item.get("payment_date"),
                        amount=float(item["amount"]),
                        paid_amount=float(item["paid_amount"]),
                        outstanding_amount=float(item["outstanding_amount"]),
                        status=str(item["status"]),
                        aging_days=int(item["aging_days"]),
                    )
                elif template == "cashflow":
                    ok = self.import_repository.persist_financial_fact(
                        job_id=job_id,
                        company_id=company_id,
                        source_system=source_system,
                        source_record_id=source_record_id,
                        period_ref=str(item["period_ref"]),
                        transaction_date=item["transaction_date"],
                        cash_flow_type=str(item["cash_flow_type"]),
                        account_type=str(item["account_type"]),
                        cash_in_amount=float(item["cash_in_amount"]),
                        cash_out_amount=float(item["cash_out_amount"]),
                        operating_cash_flow_amount=float(item["operating_cash_flow_amount"]),
                        description=str(item.get("description") or ""),
                    )
                elif template == "inventory":
                    ok = self.import_repository.persist_inventory_fact(
                        job_id=job_id,
                        company_id=company_id,
                        source_system=source_system,
                        source_record_id=source_record_id,
                        period_ref=str(item["period_ref"]),
                        product_id=str(item["product_id"]),
                        warehouse_id=str(item["warehouse_id"]),
                        snapshot_date=item["snapshot_date"],
                        opening_quantity=float(item["opening_quantity"]),
                        closing_quantity=float(item["closing_quantity"]),
                        average_quantity=float(item["average_quantity"]),
                        average_cost=float(item["average_cost"]),
                        inventory_value=float(item["inventory_value"]),
                        stock_turnover=float(item["stock_turnover"]),
                        days_in_inventory=float(item["days_in_inventory"]),
                    )
                else:
                    ok = self.import_repository.persist_hr_fact(
                        job_id=job_id,
                        company_id=company_id,
                        source_system=source_system,
                        source_record_id=source_record_id,
                        period_ref=str(item["period_ref"]),
                        employee_count=int(item["employee_count"]),
                        active_employee_count=int(item["active_employee_count"]),
                        terminated_employee_count=int(item["terminated_employee_count"]),
                        payroll_amount=float(item["payroll_amount"]),
                        average_salary=float(item["average_salary"]),
                        hours_worked=float(item["hours_worked"]),
                    )
                if ok:
                    seen_source_record_ids.add(source_record_id)
                    imported += 1
            except Exception:
                failed += 1

        return self._finish_and_trigger(
            company_id=company_id,
            source_system=source_system,
            template=template,
            job_id=job_id,
            records_read=len(records),
            records_imported=imported,
            records_failed=failed,
            correlation_id=correlation_id,
        )

    def _finish_and_trigger(
        self,
        *,
        company_id: str,
        source_system: str,
        template: str,
        job_id: str,
        records_read: int,
        records_imported: int,
        records_failed: int,
        correlation_id: str | None,
    ) -> TemplateIngestResult:
        status = "success" if records_imported > 0 and records_failed == 0 else "partial" if records_imported > 0 else "failed"
        self.import_repository.finish_job(
            job_id=job_id,
            total_rows=records_read,
            imported_rows=records_imported,
            failed_rows=records_failed,
            status=status,
        )
        event = self.import_repository.publish_ingest_completed(
            job_id=job_id,
            company_id=company_id,
            payload={
                "event_version": "1.0.0",
                "company_id": company_id,
                "import_job_id": job_id,
                "template": template,
                "source_system": source_system,
                "status": status,
                "total_rows": records_read,
                "imported_rows": records_imported,
                "failed_rows": records_failed,
                "canonical_schema_version": "2.0.0",
            },
        )

        pipeline_run_id: str | None = None
        if self.pipeline_coordinator is not None and status != "failed":
            try:
                run = self.pipeline_coordinator.consume_ingest_completed(
                    company_id=company_id,
                    import_job_id=job_id,
                    template=template,
                    source_system=source_system,
                    event_id=event.event_id,
                    correlation_id=correlation_id,
                )
                pipeline_run_id = getattr(run, "pipeline_run_id", None)
            except Exception:
                pipeline_run_id = None

        return TemplateIngestResult(
            template=template,
            records_read=records_read,
            records_imported=records_imported,
            records_failed=records_failed,
            import_job_id=job_id,
            ingest_event_id=event.event_id,
            pipeline_run_id=pipeline_run_id,
        )
