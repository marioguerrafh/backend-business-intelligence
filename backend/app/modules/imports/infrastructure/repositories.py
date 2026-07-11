from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.modules.imports.application.contracts import ImportInconsistency
from app.modules.imports.infrastructure.models import (
    ImportedFinancialFactModel,
    ImportedSaleFactModel,
    ImportInconsistencyModel,
    ImportJobModel,
    ImportPublishedEventModel,
)
from app.shared.infrastructure.messaging.events import IntegrationEvent


@dataclass(slots=True)
class ImportRepository:
    session: Session

    def create_job(
        self,
        *,
        company_id: str,
        template: str,
        source_system: str,
        canonical_schema_version: str,
        correlation_id: str | None,
    ) -> str:
        job_id = f"imp_{uuid4().hex[:16]}"
        self.session.add(
            ImportJobModel(
                import_job_id=job_id,
                company_id=company_id,
                template=template,
                source_system=source_system,
                canonical_schema_version=canonical_schema_version,
                status="running",
                total_rows=0,
                imported_rows=0,
                failed_rows=0,
                correlation_id=correlation_id,
                started_at=datetime.now(timezone.utc),
                finished_at=None,
            )
        )
        self.session.flush()
        return job_id

    def finish_job(
        self,
        *,
        job_id: str,
        total_rows: int,
        imported_rows: int,
        failed_rows: int,
        status: str,
    ) -> None:
        model = self.session.get(ImportJobModel, job_id)
        if model is None:
            raise ValueError("import job not found")
        model.total_rows = total_rows
        model.imported_rows = imported_rows
        model.failed_rows = failed_rows
        model.status = status
        model.finished_at = datetime.now(timezone.utc)
        self.session.flush()

    def add_inconsistency(self, *, company_id: str, job_id: str, issue: ImportInconsistency) -> None:
        self.session.add(
            ImportInconsistencyModel(
                inconsistency_id=f"inc_{uuid4().hex[:16]}",
                import_job_id=job_id,
                company_id=company_id,
                row_number=issue.row_number,
                field=issue.field,
                message=issue.message,
                raw_value=issue.raw_value,
            )
        )
        self.session.flush()

    def persist_sale_fact(
        self,
        *,
        job_id: str,
        company_id: str,
        source_system: str,
        source_record_id: str,
        transaction_date: date,
        invoice_id: str,
        invoice_line_id: str,
        product_external_id: str,
        customer_external_id: str,
        gross_revenue: float,
        tax_amount: float,
        discount_amount: float,
        return_amount: float,
        net_revenue: float,
        quantity_sold: float,
        cogs_amount: float,
    ) -> None:
        self.session.add(
            ImportedSaleFactModel(
                sale_fact_id=f"sale_{uuid4().hex[:16]}",
                import_job_id=job_id,
                company_id=company_id,
                source_system=source_system,
                source_record_id=source_record_id,
                transaction_date=transaction_date,
                invoice_id=invoice_id,
                invoice_line_id=invoice_line_id,
                product_external_id=product_external_id,
                customer_external_id=customer_external_id,
                gross_revenue=gross_revenue,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                return_amount=return_amount,
                net_revenue=net_revenue,
                quantity_sold=quantity_sold,
                cogs_amount=cogs_amount,
            )
        )
        self.session.flush()

    def persist_financial_fact(
        self,
        *,
        job_id: str,
        company_id: str,
        source_system: str,
        source_record_id: str,
        transaction_date: date,
        cash_flow_type: str,
        account_type: str,
        cash_in_amount: float,
        cash_out_amount: float,
        operating_cash_flow_amount: float,
        description: str | None,
    ) -> None:
        self.session.add(
            ImportedFinancialFactModel(
                financial_fact_id=f"fin_{uuid4().hex[:16]}",
                import_job_id=job_id,
                company_id=company_id,
                source_system=source_system,
                source_record_id=source_record_id,
                transaction_date=transaction_date,
                cash_flow_type=cash_flow_type,
                account_type=account_type,
                cash_in_amount=cash_in_amount,
                cash_out_amount=cash_out_amount,
                operating_cash_flow_amount=operating_cash_flow_amount,
                description=description,
            )
        )
        self.session.flush()

    def publish_ingest_completed(
        self,
        *,
        job_id: str,
        company_id: str,
        payload: dict[str, object],
    ) -> IntegrationEvent:
        event = IntegrationEvent(topic="ingest.completed.v1", payload=payload)
        self.session.add(
            ImportPublishedEventModel(
                event_id=event.event_id,
                import_job_id=job_id,
                company_id=company_id,
                topic=event.topic,
                payload_json=json.dumps(event.payload),
                published_at=event.occurred_at,
            )
        )
        self.session.flush()
        return event
