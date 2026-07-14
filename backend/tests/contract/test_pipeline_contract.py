from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.dependencies import get_db
from app.main import app
from app.modules.imports.infrastructure.models import ImportedSaleFactModel, ImportJobModel
from app.modules.kpi.infrastructure.models import KPIPublishedEventModel, KPIOrchestratorAuditLogModel, OrchestratorRunModel
from app.modules.pipeline.infrastructure.models import PipelineEventModel, PipelineLogModel, PipelineRunModel, PipelineStepModel
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
            KPIResultModel.__table__,
            OrchestratorRunModel.__table__,
            KPIOrchestratorAuditLogModel.__table__,
            KPIPublishedEventModel.__table__,
            PipelineRunModel.__table__,
            PipelineStepModel.__table__,
            PipelineLogModel.__table__,
            PipelineEventModel.__table__,
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
                import_job_id="imp_pipeline_contract_1",
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
                import_job_id="imp_pipeline_contract_1",
                company_id="cmp_acme",
                source_system="csv_manual",
                source_record_id="SRC-1",
                period_ref="2026-07",
                transaction_date=datetime(2026, 7, 10, tzinfo=timezone.utc).date(),
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


def _token(client: TestClient) -> str:
    response = client.post(
        "/v1/auth/login",
        json={"email": "owner@acme.com", "password": "Owner@123", "company_id": "cmp_acme"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_pipeline_internal_start_contract_shape() -> None:
    session_factory = _build_session_factory()
    _seed(session_factory)
    app.dependency_overrides[get_db] = _override_db(session_factory)

    client = TestClient(app)
    response = client.post(
        "/v1/pipeline/internal/start",
        json={
            "company_id": "cmp_acme",
            "import_job_id": "imp_pipeline_contract_1",
            "template": "sales",
            "source_system": "csv_manual",
            "correlation_id": "pipe-contract-1",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    expected = {
        "pipeline_run_id",
        "company_id",
        "import_job_id",
        "template",
        "status",
        "progress",
        "current_step",
        "started_at",
        "finished_at",
        "correlation_id",
        "reused_existing_run",
        "retry_of_pipeline_run_id",
        "attempt",
    }
    assert expected.issubset(payload.keys())

    run_id = payload["pipeline_run_id"]
    steps = client.get(f"/v1/pipeline/{run_id}/steps")
    assert steps.status_code == 200
    step_payload = steps.json()
    assert isinstance(step_payload, list)
    if step_payload:
        step_keys = {
            "step_id",
            "pipeline_run_id",
            "step_name",
            "step_order",
            "status",
            "duration_ms",
            "started_at",
            "finished_at",
            "error_message",
        }
        assert step_keys.issubset(step_payload[0].keys())

    logs = client.get(f"/v1/pipeline/{run_id}/logs")
    assert logs.status_code == 200
    assert isinstance(logs.json(), list)

    token = _token(client)
    job = client.get(
        "/v1/imports/jobs/imp_pipeline_contract_1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert job.status_code == 200
    job_payload = job.json()
    expected_job = {
        "job_id",
        "status",
        "progress",
        "current_step",
        "started_at",
        "estimated_remaining_seconds",
        "summary_updated",
    }
    assert expected_job.issubset(job_payload.keys())

    app.dependency_overrides.clear()
