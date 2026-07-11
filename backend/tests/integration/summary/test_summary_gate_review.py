from datetime import date, datetime, timezone

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
                executive_score_id="sc_acme",
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
            ExecutiveScoreModel(
                executive_score_id="sc_omega",
                company_id="cmp_omega",
                period_ref="2026-07",
                financial_score=10,
                commercial_score=10,
                operational_score=10,
                inventory_score=10,
                overall_score=10,
                score_version="v1",
                calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.add(
            TimelineSnapshotModel(
                timeline_snapshot_id="tl_1",
                company_id="cmp_acme",
                snapshot_date=date(2026, 7, 10),
                overall_score=80,
                financial_score=80,
                commercial_score=80,
                operational_score=80,
                top_risks_json=[],
                created_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.commit()


def test_summary_gate_review_security_and_audit() -> None:
    _summary_cache.clear()
    session_factory = _build_session_factory()
    _seed(session_factory)

    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)

    token = _token(client, company_id="cmp_acme")

    allowed = client.get(
        "/v1/summary?period_ref=2026-07",
        headers={"Authorization": f"Bearer {token}", "X-Correlation-ID": "gate-1"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["company_id"] == "cmp_acme"

    blocked = client.get(
        "/v1/summary?company_id=cmp_omega&period_ref=2026-07",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert blocked.status_code == 403

    with session_factory() as session:
        audits = session.execute(select(SummaryAuditLogModel)).scalars().all()
        assert len(audits) == 1
        assert audits[0].correlation_id == "gate-1"

    app.dependency_overrides.clear()
