from datetime import date, datetime, timedelta, timezone
from time import perf_counter

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
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


def _seed(session_factory) -> None:
    with session_factory() as session:
        session.add(
            ExecutiveScoreModel(
                executive_score_id="sc_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                financial_score=81.0,
                commercial_score=79.0,
                operational_score=78.0,
                inventory_score=77.0,
                overall_score=80.0,
                score_version="v1",
                calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.add(
            KPIResultModel(
                kpi_result_id="k1",
                company_id="cmp_acme",
                period_ref="2026-07",
                kpi_id="FIN-01",
                kpi_name="receita_liquida",
                value=1635916.85,
                unit="BRL",
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
                kpi_id="FIN-01",
                rule_id="r.fin01.net_revenue_below_target",
                severity="MEDIUM",
                priority="p1",
                alert_title="FIN-01 - receita_liquida_abaixo_meta",
                alert_description="Rule r.fin01...",
                metric_value=186000.0,
                fired_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                orchestrator_run_id="run_rule_1",
            )
        )
        session.add(
            InsightResultModel(
                insight_result_id="in_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                insight_type="trend",
                statement="Margem recuperou 1.5 p.p.",
                evidence_json={"delta": 1.5},
                generated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.add(
            RecommendationResultModel(
                recommendation_result_id="rec_res_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                recommendation_id="rec.cash.001",
                title="Negociar prazo com fornecedores",
                rank_score=0.9,
                expected_impact_json={"value": 12000, "unit": "BRL"},
                owner_role="cfo",
                sla_target="7d",
                generated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        for idx, days in enumerate([0, 1, 30, 365], start=1):
            session.add(
                TimelineSnapshotModel(
                    timeline_snapshot_id=f"tl_{idx}",
                    company_id="cmp_acme",
                    snapshot_date=date(2026, 7, 10) - timedelta(days=days),
                    overall_score=80.0 - idx,
                    financial_score=81.0 - idx,
                    commercial_score=79.0 - idx,
                    operational_score=78.0 - idx,
                    top_risks_json=[{"risk_code": "cash.low", "probability": 0.8}],
                    created_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                )
            )

        session.add(
            ExecutiveScoreModel(
                executive_score_id="sc_2",
                company_id="cmp_omega",
                period_ref="2026-07",
                financial_score=10.0,
                commercial_score=10.0,
                operational_score=10.0,
                inventory_score=10.0,
                overall_score=10.0,
                score_version="v1",
                calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.commit()


def test_summary_endpoint_composes_single_payload_and_audits() -> None:
    _summary_cache.clear()
    session_factory = _build_session_factory()
    _seed(session_factory)

    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)

    token = _token(client)
    response = client.get(
        "/v1/summary?period_ref=2026-07",
        headers={"Authorization": f"Bearer {token}", "X-Correlation-ID": "corr-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["company_id"] == "cmp_acme"
    assert payload["hero"]["title"] == "Saude da Empresa"
    assert len(payload["highlights"]) == 4
    assert payload["sections"][0]["type"] == "hero"
    assert payload["scores"]["executive_score"]["overall"] == 80.0
    assert payload["scores"]["executive_score"]["status"]
    assert len(payload["kpis"]) == 1
    assert payload["kpis"][0]["id"] == "FIN-01"
    assert payload["kpis"][0]["title"] == "Receita Liquida"
    assert payload["kpis"][0]["display_value"].startswith("R$")
    assert len(payload["alerts"]) == 1
    assert payload["alerts"][0]["severity"]["code"] == "MEDIUM"
    assert "Rule" not in payload["alerts"][0]["message"]
    assert len(payload["insights"]) == 1
    assert payload["insights"][0]["title"]
    assert len(payload["recommendations"]) == 1
    assert payload["recommendations"][0]["action_button"]
    assert payload["timeline"]["points"][0]["formatted_date"]
    assert payload["timeline"]["points"][0]["formatted_label"]
    assert payload["trends"]["monthly"]["display"]
    assert payload["trends"]["monthly"]["trend_icon"]
    assert payload["next_risks"][0]["probability"] == "80%"

    with session_factory() as session:
        audits = session.execute(select(SummaryAuditLogModel)).scalars().all()
        assert len(audits) == 1
        assert audits[0].company_id == "cmp_acme"
        assert audits[0].cache_hit is False

    app.dependency_overrides.clear()


def test_summary_enforces_tenant_scope() -> None:
    _summary_cache.clear()
    session_factory = _build_session_factory()
    _seed(session_factory)

    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)

    token = _token(client, company_id="cmp_acme")
    response = client.get(
        "/v1/summary?company_id=cmp_omega&period_ref=2026-07",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    app.dependency_overrides.clear()


def test_summary_cache_supports_latency_target() -> None:
    _summary_cache.clear()
    session_factory = _build_session_factory()
    _seed(session_factory)

    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    first_start = perf_counter()
    first = client.get("/v1/summary?period_ref=2026-07", headers=headers)
    first_elapsed = perf_counter() - first_start
    assert first.status_code == 200

    second_start = perf_counter()
    second = client.get("/v1/summary?period_ref=2026-07", headers=headers)
    second_elapsed = perf_counter() - second_start
    assert second.status_code == 200

    # Regression guard for the documented SLO target with cache warm.
    assert second_elapsed < 0.7

    with session_factory() as session:
        audits = session.execute(select(SummaryAuditLogModel).order_by(SummaryAuditLogModel.requested_at.asc())).scalars().all()
        assert len(audits) == 2
        assert audits[1].cache_hit is True

    app.dependency_overrides.clear()
