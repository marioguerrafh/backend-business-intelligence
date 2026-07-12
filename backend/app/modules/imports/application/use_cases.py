from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Protocol

from app.modules.business.application.contracts import UpsertCustomerCommand
from app.modules.business.application.product_contracts import UpsertProductCommand
from app.modules.business.domain.product_value_objects import ProductExternalReference, ProductStatus
from app.modules.business.domain.value_objects import (
    BillingAddress,
    ContactChannel,
    ContactChannelType,
    CustomerStatus,
    ExternalReference,
)
from app.modules.imports.application.contracts import (
    ImportCsvCommand,
    ImportCsvResult,
    ImportInconsistency,
)
from app.modules.imports.application.fact_mappers import (
    AccountsPayableMapper,
    AccountsReceivableMapper,
    BalanceSheetMapper,
    CashflowMapper,
    HrMapper,
    IncomeStatementMapper,
    InventoryMapper,
    SalesMapper,
)
from app.modules.imports.application.template_registry import get_template
from app.modules.imports.domain.entities import CsvRow


class PublishedEventPort(Protocol):
    event_id: str


class ImportRepositoryPort(Protocol):
    def create_job(
        self,
        *,
        company_id: str,
        template: str,
        source_system: str,
        canonical_schema_version: str,
        correlation_id: str | None,
    ) -> str:
        ...

    def finish_job(
        self,
        *,
        job_id: str,
        total_rows: int,
        imported_rows: int,
        failed_rows: int,
        status: str,
    ) -> None:
        ...

    def add_inconsistency(self, *, company_id: str, job_id: str, issue: ImportInconsistency) -> None:
        ...

    def persist_sale_fact(self, **kwargs) -> bool:
        ...

    def persist_financial_fact(self, **kwargs) -> bool:
        ...

    def persist_balance_sheet_fact(self, **kwargs) -> bool:
        ...

    def persist_income_statement_fact(self, **kwargs) -> bool:
        ...

    def persist_accounts_receivable_fact(self, **kwargs) -> bool:
        ...

    def persist_accounts_payable_fact(self, **kwargs) -> bool:
        ...

    def persist_inventory_fact(self, **kwargs) -> bool:
        ...

    def persist_hr_fact(self, **kwargs) -> bool:
        ...

    def publish_ingest_completed(
        self,
        *,
        job_id: str,
        company_id: str,
        payload: dict[str, object],
    ) -> PublishedEventPort:
        ...


class UpsertCustomerPort(Protocol):
    def execute(self, command: UpsertCustomerCommand):
        ...


class UpsertProductPort(Protocol):
    def execute(self, command: UpsertProductCommand):
        ...


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
    ):
        ...


@dataclass(slots=True)
class ImportCsvUseCase:
    repository: ImportRepositoryPort
    upsert_customer: UpsertCustomerPort
    upsert_product: UpsertProductPort
    pipeline_coordinator: PipelineCoordinatorPort | None = None
    _fact_mappers: dict[str, object] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._fact_mappers = {
            "sales": SalesMapper(),
            "cashflow": CashflowMapper(),
            "balance_sheet": BalanceSheetMapper(),
            "income_statement": IncomeStatementMapper(),
            "accounts_receivable": AccountsReceivableMapper(),
            "accounts_payable": AccountsPayableMapper(),
            "inventory": InventoryMapper(),
            "hr": HrMapper(),
        }

    def execute(self, command: ImportCsvCommand) -> ImportCsvResult:
        job_id = self.repository.create_job(
            company_id=command.company_id,
            template=command.template,
            source_system=command.source_system,
            canonical_schema_version=command.canonical_schema_version,
            correlation_id=command.correlation_id,
        )

        rows, header_issues = self._parse_rows(command)
        inconsistencies = list(header_issues)

        imported_rows = 0
        failed_rows = 0
        seen_row_keys: set[str] = set()

        for row in rows:
            try:
                dedupe_key = self._import_row(command=command, job_id=job_id, row=row)
                if dedupe_key and dedupe_key in seen_row_keys:
                    raise ValueError(f"row {row.row_number}: duplicate row key '{dedupe_key}' in CSV")
                if dedupe_key:
                    seen_row_keys.add(dedupe_key)
                imported_rows += 1
            except ValueError as exc:
                failed_rows += 1
                inconsistencies.append(
                    ImportInconsistency(
                        row_number=row.row_number,
                        field="row",
                        message=str(exc),
                    )
                )

        for issue in inconsistencies:
            self.repository.add_inconsistency(company_id=command.company_id, job_id=job_id, issue=issue)

        total_rows = len(rows)
        failed_rows += len(header_issues)
        status = self._status(total_rows=total_rows, imported_rows=imported_rows)

        self.repository.finish_job(
            job_id=job_id,
            total_rows=total_rows,
            imported_rows=imported_rows,
            failed_rows=failed_rows,
            status=status,
        )

        event = self.repository.publish_ingest_completed(
            job_id=job_id,
            company_id=command.company_id,
            payload={
                "event_version": "1.0.0",
                "company_id": command.company_id,
                "import_job_id": job_id,
                "template": command.template,
                "source_system": command.source_system,
                "status": status,
                "total_rows": total_rows,
                "imported_rows": imported_rows,
                "failed_rows": failed_rows,
                "canonical_schema_version": command.canonical_schema_version,
            },
        )

        if self.pipeline_coordinator is not None and status != "failed":
            try:
                self.pipeline_coordinator.consume_ingest_completed(
                    company_id=command.company_id,
                    import_job_id=job_id,
                    template=command.template,
                    source_system=command.source_system,
                    event_id=event.event_id,
                    correlation_id=command.correlation_id,
                )
            except Exception:
                # Import consistency takes precedence; pipeline execution can be retried by internal API.
                pass

        return ImportCsvResult(
            job_id=job_id,
            template=command.template,
            status=status,
            total_rows=total_rows,
            imported_rows=imported_rows,
            failed_rows=failed_rows,
            inconsistencies=tuple(inconsistencies),
            ingest_event_id=event.event_id,
        )

    def _parse_rows(self, command: ImportCsvCommand) -> tuple[list[CsvRow], list[ImportInconsistency]]:
        reader = csv.DictReader(command.csv_content.splitlines())
        if reader.fieldnames is None:
            raise ValueError("csv has no header")

        definition = get_template(command.template)
        missing = [field for field in definition.required_headers if field not in reader.fieldnames]
        issues: list[ImportInconsistency] = []
        if missing:
            issues.append(
                ImportInconsistency(
                    row_number=0,
                    field="header",
                    message=f"missing required columns: {', '.join(missing)}",
                )
            )
            return [], issues

        rows: list[CsvRow] = []
        for idx, item in enumerate(reader, start=2):
            rows.append(
                CsvRow(
                    row_number=idx,
                    data={key: (value or "").strip() for key, value in item.items() if key is not None},
                )
            )
        return rows, issues

    def _import_row(self, *, command: ImportCsvCommand, job_id: str, row: CsvRow) -> str | None:
        if command.template == "customers":
            self._import_customer(command=command, row=row)
            return None
        if command.template == "products":
            self._import_product(command=command, row=row)
            return None
        return self._import_fact(command=command, job_id=job_id, row=row)

    def _import_customer(self, *, command: ImportCsvCommand, row: CsvRow) -> None:
        source_record_id = self._required(row, "source_record_id")
        legal_name = self._required(row, "legal_name")
        status = CustomerStatus(self._required(row, "status").lower())

        address = None
        if row.data.get("billing_street") and row.data.get("billing_city"):
            address = BillingAddress(
                street=self._required(row, "billing_street"),
                number=row.data.get("billing_number") or None,
                district=row.data.get("billing_district") or None,
                city=self._required(row, "billing_city"),
                state=self._required(row, "billing_state"),
                country=self._required(row, "billing_country"),
                postal_code=row.data.get("billing_postal_code") or None,
            )

        contacts: list[ContactChannel] = []
        if row.data.get("contact_email"):
            contacts.append(ContactChannel(channel_type=ContactChannelType.EMAIL, value=row.data["contact_email"]))
        if row.data.get("contact_phone"):
            contacts.append(ContactChannel(channel_type=ContactChannelType.PHONE, value=row.data["contact_phone"]))

        external_refs: tuple[ExternalReference, ...] = ()
        if row.data.get("external_id"):
            external_refs = (
                ExternalReference(source_system=command.source_system, external_id=row.data["external_id"]),
            )

        self.upsert_customer.execute(
            UpsertCustomerCommand(
                company_id=command.company_id,
                legal_name=legal_name,
                trade_name=row.data.get("trade_name") or None,
                document_number=row.data.get("document_number") or None,
                status=status,
                billing_address=address,
                contacts=tuple(contacts),
                external_refs=external_refs,
                source_system=command.source_system,
                source_record_id=source_record_id,
                canonical_schema_version=command.canonical_schema_version,
                correlation_id=command.correlation_id,
            )
        )

    def _import_product(self, *, command: ImportCsvCommand, row: CsvRow) -> None:
        source_record_id = self._required(row, "source_record_id")
        external_refs: tuple[ProductExternalReference, ...] = ()
        if row.data.get("external_id"):
            external_refs = (
                ProductExternalReference(source_system=command.source_system, external_id=row.data["external_id"]),
            )

        self.upsert_product.execute(
            UpsertProductCommand(
                company_id=command.company_id,
                sku=self._required(row, "sku"),
                name=self._required(row, "name"),
                category=row.data.get("category") or None,
                unit_of_measure=self._required(row, "unit_of_measure"),
                status=ProductStatus(self._required(row, "status").lower()),
                default_cost=self._decimal_required(row, "default_cost"),
                default_price=self._decimal_required(row, "default_price"),
                tax_profile_ref=row.data.get("tax_profile_ref") or None,
                external_refs=external_refs,
                source_system=command.source_system,
                source_record_id=source_record_id,
                canonical_schema_version=command.canonical_schema_version,
                correlation_id=command.correlation_id,
            )
        )

    def _import_sale_fact(self, *, command: ImportCsvCommand, job_id: str, row: CsvRow) -> None:
        mapper = self._fact_mappers["sales"]
        record = mapper.map(command_company_id=command.company_id, row=row)
        self.repository.persist_sale_fact(
            job_id=job_id,
            source_system=command.source_system,
            **record.payload,
        )

    def _import_fact(self, *, command: ImportCsvCommand, job_id: str, row: CsvRow) -> str:
        template = self._normalize_template(command.template)
        mapper = self._fact_mappers.get(template)
        if mapper is None:
            raise ValueError(f"unsupported import template: {command.template}")

        record = mapper.map(command_company_id=command.company_id, row=row)

        if template == "sales":
            self.repository.persist_sale_fact(
                job_id=job_id,
                source_system=command.source_system,
                **record.payload,
            )
            return record.identity

        if template == "cashflow":
            self.repository.persist_financial_fact(
                job_id=job_id,
                source_system=command.source_system,
                **record.payload,
            )
            return record.identity

        if template == "balance_sheet":
            self.repository.persist_balance_sheet_fact(
                job_id=job_id,
                source_system=command.source_system,
                **record.payload,
            )
            return record.identity

        if template == "income_statement":
            self.repository.persist_income_statement_fact(
                job_id=job_id,
                source_system=command.source_system,
                **record.payload,
            )
            return record.identity

        if template == "accounts_receivable":
            self.repository.persist_accounts_receivable_fact(
                job_id=job_id,
                source_system=command.source_system,
                **record.payload,
            )
            return record.identity

        if template == "accounts_payable":
            self.repository.persist_accounts_payable_fact(
                job_id=job_id,
                source_system=command.source_system,
                **record.payload,
            )
            return record.identity

        if template == "inventory":
            self.repository.persist_inventory_fact(
                job_id=job_id,
                source_system=command.source_system,
                **record.payload,
            )
            return record.identity

        if template == "hr":
            self.repository.persist_hr_fact(
                job_id=job_id,
                source_system=command.source_system,
                **record.payload,
            )
            return record.identity

        raise ValueError(f"unsupported import template: {command.template}")

    @staticmethod
    def _normalize_template(template: str) -> str:
        if template == "financial":
            return "cashflow"
        return template

    @staticmethod
    def _required(row: CsvRow, field: str) -> str:
        value = (row.data.get(field) or "").strip()
        if not value:
            raise ValueError(f"row {row.row_number}: {field} is required")
        return value

    @staticmethod
    def _decimal_required(row: CsvRow, field: str) -> Decimal:
        value = (row.data.get(field) or "").strip()
        if not value:
            raise ValueError(f"row {row.row_number}: {field} is required")
        normalized = value.replace(",", ".")
        try:
            return Decimal(normalized)
        except InvalidOperation as exc:
            raise ValueError(f"row {row.row_number}: invalid decimal in {field}") from exc

    @staticmethod
    def _date_required(row: CsvRow, field: str) -> date:
        value = (row.data.get(field) or "").strip()
        if not value:
            raise ValueError(f"row {row.row_number}: {field} is required")
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"row {row.row_number}: invalid ISO date in {field}") from exc

    @staticmethod
    def _status(*, total_rows: int, imported_rows: int) -> str:
        if total_rows == 0 or imported_rows == 0:
            return "failed"
        if imported_rows == total_rows:
            return "success"
        return "partial"
