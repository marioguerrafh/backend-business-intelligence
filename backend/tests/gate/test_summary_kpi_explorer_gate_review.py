from datetime import date, datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.dependencies import get_db
from app.main import app
from app.modules.recommendation.infrastructure.models import RecommendationAuditLogModel
from app.modules.rule.infrastructure.models import RuleResultModel
from app.modules.summary.infrastructure.models import (
    ExecutiveScoreModel,
    InsightResultModel,
    KPIResultModel,
    RecommendationResultModel,
    SummaryProjectionModel,
    SummaryAuditLogModel,
    TimelineSnapshotModel,
)
from app.modules.summary.infrastructure.container import _summary_cache
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
            ExecutiveScoreModel.__table__,
            SummaryProjectionModel.__table__,
            KPIResultModel.__table__,
            RuleResultModel.__table__,
            InsightResultModel.__table__,
            RecommendationResultModel.__table__,
            RecommendationAuditLogModel.__table__,
            TimelineSnapshotModel.__table__,
            SummaryAuditLogModel.__table__,
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


def _token(client: TestClient, company_id: str) -> str:
    response = client.post(
        "/v1/auth/login",
        json={"email": "owner@acme.com", "password": "Owner@123", "company_id": company_id},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _seed(session_factory) -> None:
    with session_factory() as session:
        session.add(
            ExecutiveScoreModel(
                executive_score_id="sc_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                financial_score=80,
                commercial_score=80,
                operational_score=80,
                inventory_score=80,
                overall_score=80,
                score_version="v1",
                calculated_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
            )
        )
        session.add(
            KPIResultModel(
                kpi_result_id="k_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                kpi_id="FIN-01",
                kpi_name="Receita Liquida",
                value=1500,
                unit="BRL",
                trend="up",
                health="green",
                calculated_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
            )
        )
        session.add(
            ExecutiveScoreModel(
                executive_score_id="sc_2",
                company_id="cmp_omega",
                period_ref="2026-07",
                financial_score=10,
                commercial_score=10,
                operational_score=10,
                inventory_score=10,
                overall_score=10,
                score_version="v1",
                calculated_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
            )
        )
        session.add(
            TimelineSnapshotModel(
                timeline_snapshot_id="tl_1",
                company_id="cmp_acme",
                snapshot_date=date(2026, 7, 13),
                overall_score=80,
                financial_score=80,
                commercial_score=80,
                operational_score=80,
                top_risks_json=[],
                created_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
            )
        )
        session.commit()


def test_gate_summary_and_kpi_explorer_contract_and_tenant_security() -> None:
    _summary_cache.clear()
    session_factory = _build_session_factory()
    _seed(session_factory)

    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)
    token = _token(client, "cmp_acme")
    headers = {"Authorization": f"Bearer {token}", "X-Correlation-ID": "gate-kpi-1"}

    summary = client.get("/v1/summary?period_ref=2026-07", headers=headers)
    assert summary.status_code == 200
    summary_payload = summary.json()
    assert summary_payload["kpis"] == summary_payload["top_kpis"]
    assert summary_payload["kpi_overview"]["total"] >= 1
    assert summary_payload["timeline"]["points"]
    assert len({p["formatted_date"] for p in summary_payload["timeline"]["points"]}) == len(
        summary_payload["timeline"]["points"]
    )
    assert summary_payload["dashboard"]["formula_dsl_version"]
    assert summary_payload["dashboard"]["kpi_catalog_version"]
    assert summary_payload["dashboard"]["canonical_model_version"]
    assert summary_payload["dashboard"]["pipeline_version"]
    if summary_payload["alerts"]:
        assert summary_payload["alerts"][0]["kpi_id"]
        assert summary_payload["alerts"][0]["kpi_name"] not in {"KPI", "Indicador"}

    list_response = client.get("/v1/kpis?period_ref=2026-07", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()["categories"]) >= 1

    blocked = client.get("/v1/kpis?company_id=cmp_omega&period_ref=2026-07", headers=headers)
    assert blocked.status_code == 403

    app.dependency_overrides.clear()
