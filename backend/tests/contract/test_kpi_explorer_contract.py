from datetime import date, datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.dependencies import get_db
from app.main import app
from app.modules.recommendation.infrastructure.models import RecommendationAuditLogModel
from app.modules.rule.infrastructure.models import RuleResultModel
from app.modules.summary.infrastructure.models import InsightResultModel, KPIResultModel, RecommendationResultModel, TimelineSnapshotModel
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


def _token(client: TestClient) -> str:
    response = client.post(
        "/v1/auth/login",
        json={"email": "owner@acme.com", "password": "Owner@123", "company_id": "cmp_acme"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_kpi_explorer_contract_shapes() -> None:
    session_factory = _build_session_factory()
    with session_factory() as session:
        session.add(
            KPIResultModel(
                kpi_result_id="k_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                kpi_id="FIN-01",
                kpi_name="Receita Liquida",
                value=1000.0,
                unit="BRL",
                trend="up",
                health="green",
                calculated_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
            )
        )
        session.add(
            TimelineSnapshotModel(
                timeline_snapshot_id="t_1",
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

    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/v1/kpis?period_ref=2026-07", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert {"company_id", "period_ref", "categories"}.issubset(payload.keys())
    first_category = payload["categories"][0]
    assert {"id", "label", "icon", "items"}.issubset(first_category.keys())

    detail = client.get("/v1/kpis/FIN-01?period_ref=2026-07", headers=headers)
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert {"id", "name", "formula", "current_value", "history", "timeline"}.issubset(detail_payload.keys())

    catalog = client.get("/v1/kpis/catalog", headers=headers)
    assert catalog.status_code == 200
    catalog_payload = catalog.json()
    assert {"total", "categories"}.issubset(catalog_payload.keys())

    app.dependency_overrides.clear()
