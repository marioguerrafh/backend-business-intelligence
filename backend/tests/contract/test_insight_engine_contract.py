from fastapi.testclient import TestClient
from sqlalchemy import Table, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from typing import cast

from app.config.dependencies import get_db
from app.main import app
from app.modules.insight.infrastructure.models import InsightAuditLogModel, InsightPublishedEventModel
from app.modules.rule.infrastructure.models import RuleResultModel
from app.modules.summary.infrastructure.models import InsightResultModel, KPIResultModel, RecommendationResultModel
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
            InsightAuditLogModel.__table__,
            InsightPublishedEventModel.__table__,
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


def test_insight_contract_shape() -> None:
    session_factory = _build_session_factory()
    app.dependency_overrides[get_db] = _override_db(session_factory)

    client = TestClient(app)
    response = client.post(
        "/v1/insight/internal/generate",
        json={
            "company_id": "cmp_acme",
            "period_ref": "2026-07",
            "orchestrator_run_id": "run_contract_ins_1",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    expected = {
        "company_id",
        "period_ref",
        "orchestrator_run_id",
        "generated_count",
        "published_event_ids",
    }
    assert expected.issubset(payload.keys())

    app.dependency_overrides.clear()
