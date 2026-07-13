from datetime import date, datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.dependencies import get_db
from app.main import app
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
from app.modules.summary.infrastructure.container import _summary_cache
from app.shared.infrastructure.db.base import Base


REQUIRED_TOP_LEVEL_KEYS = {
    "summary_id",
    "company_id",
    "period_ref",
    "generated_at",
    "hero",
    "highlights",
    "sections",
    "scores",
    "kpis",
    "alerts",
    "insights",
    "recommendations",
    "trends",
    "next_risks",
    "timeline",
        "top_kpis",
        "kpi_overview",
}


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
            KPIResultModel.__table__,
            RuleResultModel.__table__,
            InsightResultModel.__table__,
            RecommendationResultModel.__table__,
            TimelineSnapshotModel.__table__,
            SummaryProjectionModel.__table__,
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


def _token(client: TestClient) -> str:
    response = client.post(
        "/v1/auth/login",
        json={"email": "owner@acme.com", "password": "Owner@123", "company_id": "cmp_acme"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_summary_contract_v1_shape_is_stable() -> None:
    _summary_cache.clear()
    session_factory = _build_session_factory()
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
                calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.add(
            KPIResultModel(
                kpi_result_id="k_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                kpi_id="kpi.margin",
                kpi_name="Margem",
                value=20,
                unit="%",
                trend="up",
                health="green",
                calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.add(
            RuleResultModel(
                rule_result_id="rr_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                kpi_id="FIN-03",
                rule_id="rule.cash",
                severity="HIGH",
                priority="p1",
                alert_title="Risco de caixa",
                alert_description="desc",
                metric_value=-100.0,
                fired_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                orchestrator_run_id="run_rule_1",
            )
        )
        session.add(
            InsightResultModel(
                insight_result_id="i_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                insight_type="risk",
                statement="Atenção no caixa",
                evidence_json={"score": 80},
                generated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.add(
            RecommendationResultModel(
                recommendation_result_id="rr_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                recommendation_id="rec.cash.001",
                title="Renegociar prazo",
                rank_score=0.9,
                expected_impact_json={"value": 9000, "unit": "BRL"},
                owner_role="cfo",
                sla_target="7d",
                generated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.add(
            TimelineSnapshotModel(
                timeline_snapshot_id="t_1",
                company_id="cmp_acme",
                snapshot_date=date(2026, 7, 10),
                overall_score=80,
                financial_score=80,
                commercial_score=80,
                operational_score=80,
                top_risks_json=[{"risk_code": "cash.low"}],
                created_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.commit()

    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)

    token = _token(client)
    response = client.get(
        "/v1/summary?period_ref=2026-07",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert REQUIRED_TOP_LEVEL_KEYS.issubset(payload.keys())
    assert isinstance(payload["scores"]["executive_score"]["overall"], (int, float))
    assert isinstance(payload["scores"]["executive_score"]["status"], str)
    assert isinstance(payload["hero"]["last_updated"], str)
    assert isinstance(payload["highlights"], list)
    assert payload["sections"][0]["type"] == "hero"
    assert isinstance(payload["top_kpis"], list)
    assert payload["kpis"] == payload["top_kpis"]
    assert isinstance(payload["kpis"], list)
    assert "id" in payload["top_kpis"][0]
    assert "display_value" in payload["top_kpis"][0]
    assert "display_name" in payload["top_kpis"][0]
    assert payload["kpi_overview"]["total"] >= 1
    assert payload["kpi_overview"]["categories"]
    assert "average_score" in payload["kpi_overview"]["categories"][0]
    assert "top_kpi" in payload["kpi_overview"]["categories"][0]
    assert "worst_kpi" in payload["kpi_overview"]["categories"][0]
    assert isinstance(payload["alerts"], list)
    assert payload["alerts"][0]["severity"]
    assert "severity_meta" in payload["alerts"][0]
    assert payload["alerts"][0]["kpi_name"]
    assert payload["alerts"][0]["kpi_id"]
    assert payload["alerts"][0]["rule_id"]
    assert payload["alerts"][0]["rule_name"]
    assert "related_recommendation_ids" in payload["alerts"][0]
    assert "message" in payload["alerts"][0]
    assert "icon" in payload["alerts"][0]
    assert payload["alerts"][0]["kpi_name"] not in {"KPI", "Indicador"}
    assert isinstance(payload["insights"], list)
    assert "summary" in payload["insights"][0]
    assert "related_kpis" in payload["insights"][0]
    assert "related_rules" in payload["insights"][0]
    assert "related_recommendations" in payload["insights"][0]
    assert isinstance(payload["recommendations"], list)
    assert "action_button" in payload["recommendations"][0]
    assert payload["recommendations"][0]["estimated_gain"]
    assert payload["recommendations"][0]["owner"]
    assert payload["recommendations"][0]["related_kpis"]
    assert payload["recommendations"][0]["related_rules"]
    assert payload["recommendations"][0]["priority_score"] > 0
    assert isinstance(payload["next_risks"], list)
    assert "probability" in payload["next_risks"][0]
    assert "points" in payload["timeline"]
    assert "formatted_date" in payload["timeline"]["points"][0]
    assert "formatted_label" in payload["timeline"]["points"][0]
    assert "trend_icon" in payload["trends"]["monthly"]
    assert payload["hero"]["alerts_active"] >= 0
    assert payload["hero"]["recommendations_active"] >= 0
    assert payload["hero"]["insights_generated"] >= 0
    assert payload["hero"]["kpis_calculated"] >= 0
    assert payload["hero"]["rules_triggered"] >= 0
    assert payload["hero"]["pipeline_status"]
    assert payload["hero"]["confidence_score"] > 0
    assert payload["dashboard"]["formula_dsl_version"]
    assert payload["dashboard"]["kpi_catalog_version"]
    assert payload["dashboard"]["canonical_model_version"]
    assert payload["dashboard"]["pipeline_version"]

    app.dependency_overrides.clear()
