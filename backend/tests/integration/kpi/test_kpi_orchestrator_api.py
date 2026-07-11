from datetime import date, datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import Table, create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from typing import cast

from app.config.dependencies import get_db
from app.main import app
from app.modules.imports.infrastructure.models import ImportedSaleFactModel, ImportJobModel
from app.modules.kpi.infrastructure.models import KPIPublishedEventModel, KPIOrchestratorAuditLogModel, OrchestratorRunModel
from app.modules.summary.infrastructure.models import KPIResultModel
from app.shared.infrastructure.db.base import Base


def _build_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = cast(
        list[Table],
        [
            ImportJobModel.__table__,
            ImportedSaleFactModel.__table__,
            KPIResultModel.__table__,
            OrchestratorRunModel.__table__,
            KPIOrchestratorAuditLogModel.__table__,
            KPIPublishedEventModel.__table__,
        ],
    )
    Base.metadata.create_all(bind=engine, tables=tables)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _override_db(session_factory):
    def _dep():
        db: Session = session_factory()
        try:
            yield db
        finally:
            db.close()

    return _dep


def _seed_import_data(session_factory) -> None:
    with session_factory() as session:
        session.add(
            ImportJobModel(
                import_job_id="imp_001",
                company_id="cmp_acme",
                template="sales",
                source_system="csv_manual",
                canonical_schema_version="1.0.0",
                status="success",
                total_rows=2,
                imported_rows=2,
                failed_rows=0,
                correlation_id="corr_1",
                started_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                finished_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.add(
            ImportedSaleFactModel(
                sale_fact_id="sale_1",
                import_job_id="imp_001",
                company_id="cmp_acme",
                source_system="csv_manual",
                source_record_id="SRC-1",
                transaction_date=date(2026, 7, 10),
                invoice_id="NF-1",
                invoice_line_id="1",
                product_external_id="PRD-1",
                customer_external_id="CLI-1",
                gross_revenue=1000.0,
                tax_amount=100.0,
                discount_amount=20.0,
                return_amount=10.0,
                net_revenue=870.0,
                quantity_sold=3.0,
                cogs_amount=600.0,
            )
        )
        session.add(
            ImportedSaleFactModel(
                sale_fact_id="sale_2",
                import_job_id="imp_001",
                company_id="cmp_acme",
                source_system="csv_manual",
                source_record_id="SRC-2",
                transaction_date=date(2026, 7, 11),
                invoice_id="NF-2",
                invoice_line_id="1",
                product_external_id="PRD-2",
                customer_external_id="CLI-2",
                gross_revenue=500.0,
                tax_amount=50.0,
                discount_amount=10.0,
                return_amount=5.0,
                net_revenue=435.0,
                quantity_sold=2.0,
                cogs_amount=300.0,
            )
        )
        session.commit()


def test_kpi_orchestrator_consumes_ingest_event_and_persists_results_and_events() -> None:
    session_factory = _build_session_factory()
    _seed_import_data(session_factory)
    app.dependency_overrides[get_db] = _override_db(session_factory)

    client = TestClient(app)

    response = client.post(
        "/v1/kpi/internal/orchestrator/ingest-completed",
        json={
            "company_id": "cmp_acme",
            "import_job_id": "imp_001",
            "template": "sales",
            "source_system": "csv_manual",
            "event_id": "evt_ing_1",
            "orchestrator_run_id": "run_orc_1",
            "correlation_id": "corr_1",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_event_topic"] == "ingest.completed.v1"
    assert payload["company_id"] == "cmp_acme"
    assert len(payload["periods"]) == 1
    assert payload["periods"][0]["status"] in {"success", "partial"}
    assert payload["periods"][0]["recalculated_count"] >= 1

    with session_factory() as session:
        kpi_results = session.execute(select(KPIResultModel)).scalars().all()
        runs = session.execute(select(OrchestratorRunModel)).scalars().all()
        audits = session.execute(select(KPIOrchestratorAuditLogModel)).scalars().all()
        events = session.execute(select(KPIPublishedEventModel)).scalars().all()

        assert len(kpi_results) >= 1
        assert len(runs) == 1
        assert len(audits) >= 1
        assert len(events) >= 1
        assert events[0].topic == "kpi.recalculated.v1"

    response_idempotent = client.post(
        "/v1/kpi/internal/orchestrator/ingest-completed",
        json={
            "company_id": "cmp_acme",
            "import_job_id": "imp_001",
            "template": "sales",
            "source_system": "csv_manual",
            "event_id": "evt_ing_1",
            "orchestrator_run_id": "run_orc_1",
            "correlation_id": "corr_1",
        },
    )

    assert response_idempotent.status_code == 200
    id_payload = response_idempotent.json()
    assert id_payload["periods"][0]["idempotent_hit"] is True

    with session_factory() as session:
        events_after = session.execute(select(KPIPublishedEventModel)).scalars().all()
        assert len(events_after) == len(events)

    app.dependency_overrides.clear()
