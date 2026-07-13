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
    InsightResultModel,
    KPIResultModel,
    RecommendationResultModel,
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
    Base.metadata.create_all(
        bind=engine,
        tables=[
            KPIResultModel.__table__,
            RuleResultModel.__table__,
            InsightResultModel.__table__,
            RecommendationResultModel.__table__,
            RecommendationAuditLogModel.__table__,
            TimelineSnapshotModel.__table__,
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


def _token(client: TestClient, company_id: str = "cmp_acme") -> str:
    response = client.post(
        "/v1/auth/login",
        json={"email": "owner@acme.com", "password": "Owner@123", "company_id": company_id},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _seed(session_factory) -> None:
    with session_factory() as session:
        now = datetime(2026, 7, 13, tzinfo=timezone.utc)
        session.add(
            KPIResultModel(
                kpi_result_id="kpi_fin_01",
                company_id="cmp_acme",
                period_ref="2026-07",
                kpi_id="FIN-01",
                formula_id="revenue.net",
                kpi_name="Receita Liquida",
                value=2200.0,
                unit="BRL",
                trend="up",
                health="green",
                calculated_at=now,
            )
        )
        session.add(
            RuleResultModel(
                rule_result_id="rule_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                kpi_id="FIN-01",
                rule_id="r.fin01.net_revenue_below_target",
                severity="MEDIUM",
                priority="p1",
                alert_title="Receita abaixo da meta",
                alert_description="Receita liquida abaixo da meta definida.",
                metric_value=2200.0,
                fired_at=now,
                orchestrator_run_id="run_1",
            )
        )
        session.add(
            InsightResultModel(
                insight_result_id="ins_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                insight_type="trend",
                statement="Receita Liquida em aceleracao no periodo.",
                evidence_json={"delta": 12.0},
                generated_at=now,
            )
        )
        session.add(
            RecommendationResultModel(
                recommendation_result_id="rec_res_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                recommendation_id="rec.fin01.001",
                title="Plano de recuperacao de receita",
                rank_score=0.81,
                expected_impact_json={"value": 180.0, "unit": "BRL"},
                owner_role="revenue_manager",
                sla_target="72h",
                generated_at=now,
            )
        )
        session.add(
            RecommendationAuditLogModel(
                audit_log_id="reca_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                recommendation_id="rec.fin01.001",
                trigger_rule_id="r.fin01.net_revenue_below_target",
                status="generated",
                details_json='{"reason":"generated"}',
                orchestrator_run_id="run_1",
                created_at=now,
            )
        )
        session.add(
            TimelineSnapshotModel(
                timeline_snapshot_id="tl_1",
                company_id="cmp_acme",
                snapshot_date=date(2026, 7, 13),
                overall_score=82.0,
                financial_score=84.0,
                commercial_score=78.0,
                operational_score=76.0,
                top_risks_json=[],
                created_at=now,
            )
        )
        session.commit()


def test_kpi_explorer_list_detail_and_catalog() -> None:
    session_factory = _build_session_factory()
    _seed(session_factory)

    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    list_response = client.get("/v1/kpis?period_ref=2026-07", headers=headers)
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["period_ref"] == "2026-07"
    assert len(list_payload["categories"]) >= 1

    financial = next((item for item in list_payload["categories"] if item["id"] == "financial"), None)
    assert financial is not None
    fin_01 = next((item for item in financial["items"] if item["id"] == "FIN-01"), None)
    assert fin_01 is not None
    assert fin_01["formatted_value"].startswith("R$")

    detail_response = client.get("/v1/kpis/FIN-01?period_ref=2026-07", headers=headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == "FIN-01"
    assert detail["formula"]["formula_id"]
    assert detail["current_value"]["formatted_value"]
    assert len(detail["related_rules"]) >= 1

    catalog_response = client.get("/v1/kpis/catalog", headers=headers)
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    assert catalog["total"] >= 1
    assert len(catalog["categories"]) >= 1

    app.dependency_overrides.clear()
