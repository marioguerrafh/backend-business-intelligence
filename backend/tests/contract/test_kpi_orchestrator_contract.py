from datetime import date, datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.dependencies import get_db
from app.main import app
from app.modules.imports.infrastructure.models import (
    ImportedAccountsPayableFactModel,
    ImportedAccountsReceivableFactModel,
    ImportedBalanceSheetFactModel,
    ImportedFinancialFactModel,
    ImportedHrFactModel,
    ImportedIncomeStatementFactModel,
    ImportedInventoryFactModel,
    ImportedSaleFactModel,
    ImportJobModel,
)
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
    Base.metadata.create_all(
        bind=engine,
        tables=[
            ImportJobModel.__table__,
            ImportedSaleFactModel.__table__,
            ImportedFinancialFactModel.__table__,
            ImportedBalanceSheetFactModel.__table__,
            ImportedIncomeStatementFactModel.__table__,
            ImportedAccountsReceivableFactModel.__table__,
            ImportedAccountsPayableFactModel.__table__,
            ImportedInventoryFactModel.__table__,
            ImportedHrFactModel.__table__,
            KPIResultModel.__table__,
            OrchestratorRunModel.__table__,
            KPIOrchestratorAuditLogModel.__table__,
            KPIPublishedEventModel.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _override_db(session_factory):
    def _dep():
        db: Session = session_factory()
        try:
            yield db
        finally:
            db.close()

    return _dep


def _seed(session_factory) -> None:
    with session_factory() as session:
        session.add(
            ImportJobModel(
                import_job_id="imp_contract_1",
                company_id="cmp_acme",
                template="sales",
                source_system="csv_manual",
                canonical_schema_version="1.0.0",
                status="success",
                total_rows=1,
                imported_rows=1,
                failed_rows=0,
                correlation_id="corr_contract",
                started_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                finished_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.add(
            ImportedSaleFactModel(
                sale_fact_id="sale_contract_1",
                import_job_id="imp_contract_1",
                company_id="cmp_acme",
                source_system="csv_manual",
                source_record_id="SRC-1",
                period_ref="2026-07",
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
        session.commit()


def test_kpi_orchestrator_contract_shape() -> None:
    session_factory = _build_session_factory()
    _seed(session_factory)
    app.dependency_overrides[get_db] = _override_db(session_factory)

    client = TestClient(app)

    response = client.post(
        "/v1/kpi/internal/orchestrator/ingest-completed",
        json={
            "company_id": "cmp_acme",
            "import_job_id": "imp_contract_1",
            "template": "sales",
            "source_system": "csv_manual",
            "event_id": "evt_contract_1",
            "orchestrator_run_id": "run_contract_1",
        },
    )

    assert response.status_code == 200
    payload = response.json()

    expected_top = {
        "source_event_topic",
        "source_event_id",
        "company_id",
        "import_job_id",
        "periods",
    }
    assert expected_top.issubset(payload.keys())

    assert isinstance(payload["periods"], list)
    assert len(payload["periods"]) >= 1

    expected_period = {
        "period_ref",
        "orchestrator_run_id",
        "status",
        "recalculated_count",
        "failed_count",
        "idempotent_hit",
        "published_event_ids",
    }
    assert expected_period.issubset(payload["periods"][0].keys())

    app.dependency_overrides.clear()
