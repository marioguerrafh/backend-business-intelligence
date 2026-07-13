from datetime import date, datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.dependencies import get_db
from app.main import app
from app.modules.recommendation.infrastructure.models import RecommendationAuditLogModel
from app.modules.rule.infrastructure.models import RuleResultModel
from app.modules.summary.infrastructure.container import _summary_cache
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
    Base.metadata.create_all(
        bind=engine,
        tables=[
            ExecutiveScoreModel.__table__,
            KPIResultModel.__table__,
            RuleResultModel.__table__,
            InsightResultModel.__table__,
            RecommendationResultModel.__table__,
            RecommendationAuditLogModel.__table__,
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


def _seed(session_factory) -> None:
    with session_factory() as session:
        session.add(
            ExecutiveScoreModel(
                executive_score_id="sc_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                financial_score=81,
                commercial_score=74,
                operational_score=68,
                inventory_score=77,
                overall_score=76,
                score_version="v1",
                calculated_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
            )
        )
        session.add_all(
            [
                KPIResultModel(
                    kpi_result_id="k_1",
                    company_id="cmp_acme",
                    period_ref="2026-07",
                    kpi_id="FIN-01",
                    kpi_name="Receita Liquida",
                    value=1800000.0,
                    unit="BRL",
                    trend="up",
                    health="green",
                    calculated_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
                ),
                KPIResultModel(
                    kpi_result_id="k_2",
                    company_id="cmp_acme",
                    period_ref="2026-07",
                    kpi_id="COM-01",
                    kpi_name="Taxa de Conversao",
                    value=12.5,
                    unit="PERCENT",
                    trend="down",
                    health="yellow",
                    calculated_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
                ),
                KPIResultModel(
                    kpi_result_id="k_3",
                    company_id="cmp_acme",
                    period_ref="2026-07",
                    kpi_id="FIN-03",
                    kpi_name="Fluxo de Caixa Operacional",
                    value=-25000.0,
                    unit="BRL",
                    trend="down",
                    health="red",
                    calculated_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
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
                priority="p1",
                alert_title="Fluxo de Caixa Operacional negativo",
                alert_description="Fluxo de Caixa Operacional ficou negativo por 3 dias.",
                metric_value=-25000,
                fired_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
                orchestrator_run_id="run_1",
            )
        )
        session.add(
            InsightResultModel(
                insight_result_id="ins_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                insight_type="risk",
                statement="Fluxo de Caixa Operacional em deterioracao continua.",
                evidence_json={"related_kpis": ["FIN-03"], "related_rules": ["r.fin03.cash_negative_3d"]},
                generated_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
            )
        )
        session.add(
            RecommendationResultModel(
                recommendation_result_id="rec_res_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                recommendation_id="rec.fin03.001",
                title="Reestruturar ciclo de caixa",
                rank_score=0.92,
                expected_impact_json={"value": 40000, "unit": "BRL"},
                owner_role="cfo",
                sla_target="7d",
                generated_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
            )
        )
        session.add(
            RecommendationAuditLogModel(
                audit_log_id="aud_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                recommendation_id="rec.fin03.001",
                trigger_rule_id="r.fin03.cash_negative_3d",
                status="ACTIVE",
                details_json="{}",
                orchestrator_run_id="run_1",
                created_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
            )
        )
        session.add_all(
            [
                TimelineSnapshotModel(
                    timeline_snapshot_id="tl_1",
                    company_id="cmp_acme",
                    snapshot_date=date(2026, 5, 31),
                    overall_score=71,
                    financial_score=72,
                    commercial_score=69,
                    operational_score=70,
                    top_risks_json=[],
                    created_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
                ),
                TimelineSnapshotModel(
                    timeline_snapshot_id="tl_2",
                    company_id="cmp_acme",
                    snapshot_date=date(2026, 6, 30),
                    overall_score=73,
                    financial_score=74,
                    commercial_score=71,
                    operational_score=72,
                    top_risks_json=[],
                    created_at=datetime(2026, 6, 30, tzinfo=timezone.utc),
                ),
                TimelineSnapshotModel(
                    timeline_snapshot_id="tl_3",
                    company_id="cmp_acme",
                    snapshot_date=date(2026, 7, 13),
                    overall_score=76,
                    financial_score=81,
                    commercial_score=74,
                    operational_score=68,
                    top_risks_json=[],
                    created_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
                ),
            ]
        )
        session.commit()


def test_summary_v4_regression_payload_has_no_placeholder_or_duplicate_timeline() -> None:
    _summary_cache.clear()
    session_factory = _build_session_factory()
    _seed(session_factory)

    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)

    token = _token(client)
    response = client.get(
        "/v1/summary?period_ref=2026-07",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["top_kpis"] == payload["kpis"]
    assert len(payload["timeline"]["points"]) == 3
    labels = [point["formatted_label"] for point in payload["timeline"]["points"]]
    assert labels == ["Mai/26", "Jun/26", "Jul/26"]

    alert = payload["alerts"][0]
    assert alert["kpi_id"] == "FIN-03"
    assert alert["kpi_name"] == "Fluxo de Caixa Operacional"
    assert alert["related_recommendation_ids"] == ["rec.fin03.001"]

    insight = payload["insights"][0]
    assert insight["related_kpis"] == ["FIN-03"]
    assert insight["related_rules"] == ["r.fin03.cash_negative_3d"]
    assert insight["related_recommendations"] == ["rec.fin03.001"]

    recommendation = payload["recommendations"][0]
    assert recommendation["related_kpis"] == ["FIN-03"]
    assert recommendation["related_rules"] == ["r.fin03.cash_negative_3d"]
    assert recommendation["priority_score"] == 0.92

    assert payload["dashboard"]["formula_dsl_version"]
    assert payload["dashboard"]["kpi_catalog_version"]
    assert payload["dashboard"]["canonical_model_version"]
    assert payload["dashboard"]["pipeline_version"]

    serialized = str(payload)
    assert "'':" not in serialized
    assert "\"\"" not in serialized
    assert alert["kpi_name"] not in {"KPI", "Indicador"}
    for item in payload["top_kpis"]:
        assert item["title"] not in {"KPI", "Indicador"}
        assert item["display_name"] not in {"KPI", "Indicador"}

    app.dependency_overrides.clear()
