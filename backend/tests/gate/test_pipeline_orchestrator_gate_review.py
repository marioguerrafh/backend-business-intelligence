from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import Table, create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from typing import cast

from app.config.dependencies import get_db
from app.main import app
from app.modules.executive_score.infrastructure.models import ExecutiveScoreAuditLogModel, ExecutiveScorePublishedEventModel
from app.modules.imports.infrastructure.models import (
    ImportedAccountsPayableFactModel,
    ImportedAccountsReceivableFactModel,
    ImportedBalanceSheetFactModel,
    ImportedFinancialFactModel,
    ImportedHrFactModel,
    ImportedIncomeStatementFactModel,
    ImportedInventoryFactModel,
    ImportedSaleFactModel,
    ImportInconsistencyModel,
    ImportJobModel,
    ImportPublishedEventModel,
)
from app.modules.insight.infrastructure.models import InsightAuditLogModel, InsightPublishedEventModel
from app.modules.kpi.infrastructure.models import KPIPublishedEventModel, KPIOrchestratorAuditLogModel, OrchestratorRunModel
from app.modules.pipeline.infrastructure.models import PipelineEventModel, PipelineLogModel, PipelineRunModel, PipelineStepModel
from app.modules.recommendation.infrastructure.models import RecommendationAuditLogModel, RecommendationPublishedEventModel
from app.modules.rule.infrastructure.models import RuleAuditLogModel, RulePublishedEventModel, RuleResultModel
from app.modules.summary.infrastructure.models import (
    ExecutiveScoreModel,
    InsightResultModel,
    KPIResultModel,
    RecommendationResultModel,
    SummaryAuditLogModel,
    SummaryProjectionModel,
    TimelineSnapshotModel,
)
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
            ImportInconsistencyModel.__table__,
            ImportedSaleFactModel.__table__,
            ImportedFinancialFactModel.__table__,
            ImportedBalanceSheetFactModel.__table__,
            ImportedIncomeStatementFactModel.__table__,
            ImportedAccountsReceivableFactModel.__table__,
            ImportedAccountsPayableFactModel.__table__,
            ImportedInventoryFactModel.__table__,
            ImportedHrFactModel.__table__,
            ImportPublishedEventModel.__table__,
            KPIResultModel.__table__,
            OrchestratorRunModel.__table__,
            KPIOrchestratorAuditLogModel.__table__,
            KPIPublishedEventModel.__table__,
            RuleResultModel.__table__,
            RuleAuditLogModel.__table__,
            RulePublishedEventModel.__table__,
            RecommendationResultModel.__table__,
            RecommendationAuditLogModel.__table__,
            RecommendationPublishedEventModel.__table__,
            InsightResultModel.__table__,
            InsightAuditLogModel.__table__,
            InsightPublishedEventModel.__table__,
            ExecutiveScoreModel.__table__,
            TimelineSnapshotModel.__table__,
            ExecutiveScoreAuditLogModel.__table__,
            ExecutiveScorePublishedEventModel.__table__,
            SummaryProjectionModel.__table__,
            SummaryAuditLogModel.__table__,
            PipelineRunModel.__table__,
            PipelineStepModel.__table__,
            PipelineLogModel.__table__,
            PipelineEventModel.__table__,
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


def _token(client: TestClient, company_id: str = "cmp_acme") -> str:
    response = client.post(
        "/v1/auth/login",
        json={
            "email": "owner@acme.com",
            "password": "Owner@123",
            "company_id": company_id,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_gate_pipeline_runs_without_manual_engine_calls() -> None:
    session_factory = _build_session_factory()
    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)

    token = _token(client)
    csv_content = (
        "company_id,period_ref,source_record_id,transaction_date,invoice_id,invoice_line_id,product_external_id,customer_external_id,"
        "gross_revenue,tax_amount,discount_amount,return_amount,net_revenue,quantity_sold,cogs_amount\n"
        "cmp_acme,2026-07,SRC-GATE-1,2026-07-10,NF-1,1,PRD-1,CLI-1,1200,120,30,20,1030,4,700\n"
    )

    import_response = client.post(
        "/v1/imports/csv",
        data={
            "company_id": "cmp_acme",
            "template": "sales",
            "source_system": "csv_manual",
        },
        files={"file": ("sales.csv", csv_content, "text/csv")},
        headers={"Authorization": f"Bearer {token}", "X-Correlation-ID": "gate-pipe-1"},
    )
    assert import_response.status_code == 200
    job_id = import_response.json()["job_id"]

    status_response = client.get(
        f"/v1/imports/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["job_id"] == job_id

    with session_factory() as session:
        run = session.execute(
            select(PipelineRunModel).where(
                PipelineRunModel.company_id == "cmp_acme",
                PipelineRunModel.import_job_id == job_id,
            )
        ).scalar_one_or_none()
        assert run is not None

        events = session.execute(
            select(PipelineEventModel).where(PipelineEventModel.pipeline_run_id == run.pipeline_run_id)
        ).scalars().all()
        topics = {evt.topic for evt in events}
        assert "pipeline.started.v1" in topics
        assert "pipeline.step.started.v1" in topics
        assert "pipeline.step.completed.v1" in topics
        assert "pipeline.completed.v1" in topics or "pipeline.failed.v1" in topics

        steps = session.execute(
            select(PipelineStepModel).where(PipelineStepModel.pipeline_run_id == run.pipeline_run_id)
        ).scalars().all()
        step_names = {step.step_name for step in steps}
        assert {
            "KPI Orchestrator",
            "Rule Engine",
            "Recommendation Engine",
            "Insight Engine",
            "Executive Score Engine",
            "Summary Engine",
        }.issubset(step_names)

        step_statuses = {step.step_name: step.status for step in steps}
        assert step_statuses.get("KPI Orchestrator") == "SUCCESS"
        assert step_statuses.get("Rule Engine") == "SUCCESS"
        assert step_statuses.get("Recommendation Engine") == "SUCCESS"
        assert step_statuses.get("Insight Engine") == "SUCCESS"
        assert step_statuses.get("Executive Score Engine") == "SUCCESS"
        assert step_statuses.get("Summary Engine") == "SUCCESS"

    app.dependency_overrides.clear()
