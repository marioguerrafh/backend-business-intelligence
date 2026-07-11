from datetime import datetime, timezone
from typing import cast

from fastapi.testclient import TestClient
from sqlalchemy import Table, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.dependencies import get_db
from app.main import app
from app.modules.executive_score.infrastructure.models import ExecutiveScoreAuditLogModel, ExecutiveScorePublishedEventModel
from app.modules.insight.infrastructure.models import InsightAuditLogModel, InsightPublishedEventModel
from app.modules.recommendation.infrastructure.models import RecommendationAuditLogModel, RecommendationPublishedEventModel
from app.modules.rule.infrastructure.models import RuleResultModel
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
            KPIResultModel.__table__,
            RuleResultModel.__table__,
            RecommendationResultModel.__table__,
            InsightResultModel.__table__,
            ExecutiveScoreModel.__table__,
            TimelineSnapshotModel.__table__,
            SummaryProjectionModel.__table__,
            SummaryAuditLogModel.__table__,
            RecommendationAuditLogModel.__table__,
            RecommendationPublishedEventModel.__table__,
            InsightAuditLogModel.__table__,
            InsightPublishedEventModel.__table__,
            ExecutiveScoreAuditLogModel.__table__,
            ExecutiveScorePublishedEventModel.__table__,
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


def _seed(session_factory) -> None:
    with session_factory() as session:
        session.add_all(
            [
                KPIResultModel(
                    kpi_result_id="k_fin03",
                    company_id="cmp_acme",
                    period_ref="2026-07",
                    period_grain="month",
                    kpi_id="FIN-03",
                    formula_id="f.fin03",
                    kpi_name="fluxo_caixa_operacional",
                    value=-1000.0,
                    unit="BRL",
                    confidence_score=1.0,
                    trend="down",
                    health="red",
                    orchestrator_run_id="run_kpi_1",
                    calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                ),
                KPIResultModel(
                    kpi_result_id="k_fin01",
                    company_id="cmp_acme",
                    period_ref="2026-07",
                    period_grain="month",
                    kpi_id="FIN-01",
                    formula_id="f.fin01",
                    kpi_name="financial",
                    value=80.0,
                    unit="score",
                    confidence_score=1.0,
                    trend="up",
                    health="green",
                    orchestrator_run_id="run_kpi_1",
                    calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                ),
                KPIResultModel(
                    kpi_result_id="k_com01",
                    company_id="cmp_acme",
                    period_ref="2026-07",
                    period_grain="month",
                    kpi_id="COM-01",
                    formula_id="f.com01",
                    kpi_name="commercial",
                    value=72.0,
                    unit="score",
                    confidence_score=1.0,
                    trend="up",
                    health="green",
                    orchestrator_run_id="run_kpi_1",
                    calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                ),
                KPIResultModel(
                    kpi_result_id="k_opr01",
                    company_id="cmp_acme",
                    period_ref="2026-07",
                    period_grain="month",
                    kpi_id="OPR-01",
                    formula_id="f.opr01",
                    kpi_name="operational",
                    value=68.0,
                    unit="score",
                    confidence_score=1.0,
                    trend="up",
                    health="green",
                    orchestrator_run_id="run_kpi_1",
                    calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                ),
                KPIResultModel(
                    kpi_result_id="k_est02",
                    company_id="cmp_acme",
                    period_ref="2026-07",
                    period_grain="month",
                    kpi_id="EST-02",
                    formula_id="f.est02",
                    kpi_name="inventory",
                    value=63.0,
                    unit="score",
                    confidence_score=1.0,
                    trend="down",
                    health="yellow",
                    orchestrator_run_id="run_kpi_1",
                    calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                ),
            ]
        )
        session.add(
            RuleResultModel(
                rule_result_id="rr_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                kpi_id="FIN-03",
                rule_id="r.fin03.cash_negative_3d",
                severity="HIGH",
                priority="p0",
                alert_title="fluxo_caixa_negativo_tres_dias",
                alert_description="desc",
                metric_value=-1000.0,
                fired_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                orchestrator_run_id="run_rule_1",
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


def test_gate_decision_engines_pipeline_and_summary() -> None:
    session_factory = _build_session_factory()
    _seed(session_factory)
    app.dependency_overrides[get_db] = _override_db(session_factory)

    client = TestClient(app)

    rec = client.post(
        "/v1/recommendation/internal/generate",
        json={"company_id": "cmp_acme", "period_ref": "2026-07", "orchestrator_run_id": "run_rec_1"},
    )
    assert rec.status_code == 200

    ins = client.post(
        "/v1/insight/internal/generate",
        json={"company_id": "cmp_acme", "period_ref": "2026-07", "orchestrator_run_id": "run_ins_1"},
    )
    assert ins.status_code == 200

    esc = client.post(
        "/v1/executive-score/internal/calculate",
        json={"company_id": "cmp_acme", "period_ref": "2026-07", "orchestrator_run_id": "run_exec_1"},
    )
    assert esc.status_code == 200

    token = _token(client)
    summary = client.get(
        "/v1/summary?period_ref=2026-07",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["scores"]["overall"] >= 0
    assert isinstance(payload["insights"], list)
    assert isinstance(payload["recommendations"], list)

    app.dependency_overrides.clear()
