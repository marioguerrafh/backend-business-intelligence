from fastapi.testclient import TestClient
from sqlalchemy import Table, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from typing import cast

from app.config.dependencies import get_db
from app.main import app
from app.modules.rule.infrastructure.models import RuleAuditLogModel, RulePublishedEventModel, RuleResultModel
from app.modules.summary.infrastructure.models import KPIResultModel
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
            RuleAuditLogModel.__table__,
            RulePublishedEventModel.__table__,
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


def test_gate_rule_engine_minimum_operational_requirements() -> None:
    session_factory = _build_session_factory()
    app.dependency_overrides[get_db] = _override_db(session_factory)

    client = TestClient(app)

    health = client.get("/v1/rule/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    execute = client.post(
        "/v1/rule/internal/execute",
        json={
            "company_id": "cmp_acme",
            "period_ref": "2026-07",
            "orchestrator_run_id": "gate_run_001",
        },
    )

    assert execute.status_code == 200

    app.dependency_overrides.clear()
