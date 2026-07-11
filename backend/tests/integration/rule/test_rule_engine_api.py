from fastapi.testclient import TestClient
from sqlalchemy import Table, create_engine, select
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


def _seed_kpis(session_factory) -> None:
    from datetime import datetime, timezone

    with session_factory() as session:
        session.add(
            KPIResultModel(
                kpi_result_id="kpi_1",
                company_id="cmp_acme",
                period_ref="2026-07-10",
                period_grain="day",
                kpi_id="FIN-03",
                formula_id="f.fin03",
                kpi_name="fluxo_caixa_operacional",
                value=-1200.0,
                unit="BRL",
                confidence_score=1.0,
                trend="down",
                health="red",
                orchestrator_run_id="run_kpi_1",
                calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.add(
            KPIResultModel(
                kpi_result_id="kpi_0",
                company_id="cmp_acme",
                period_ref="2026-07-09",
                period_grain="day",
                kpi_id="FIN-03",
                formula_id="f.fin03",
                kpi_name="fluxo_caixa_operacional",
                value=-900.0,
                unit="BRL",
                confidence_score=1.0,
                trend="down",
                health="red",
                orchestrator_run_id="run_kpi_0",
                calculated_at=datetime(2026, 7, 9, tzinfo=timezone.utc),
            )
        )
        session.add(
            KPIResultModel(
                kpi_result_id="kpi_m2",
                company_id="cmp_acme",
                period_ref="2026-07-08",
                period_grain="day",
                kpi_id="FIN-03",
                formula_id="f.fin03",
                kpi_name="fluxo_caixa_operacional",
                value=-700.0,
                unit="BRL",
                confidence_score=1.0,
                trend="down",
                health="red",
                orchestrator_run_id="run_kpi_m2",
                calculated_at=datetime(2026, 7, 8, tzinfo=timezone.utc),
            )
        )
        session.commit()


def test_rule_engine_internal_api_evaluates_and_persists_and_publishes() -> None:
    session_factory = _build_session_factory()
    _seed_kpis(session_factory)
    app.dependency_overrides[get_db] = _override_db(session_factory)

    client = TestClient(app)

    response = client.post(
        "/v1/rule/internal/execute",
        json={
            "company_id": "cmp_acme",
            "period_ref": "2026-07-10",
            "orchestrator_run_id": "run_rule_001",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["company_id"] == "cmp_acme"
    assert payload["period_ref"] == "2026-07-10"
    assert payload["evaluated_rules"] >= 1

    with session_factory() as session:
        results = session.execute(select(RuleResultModel)).scalars().all()
        audits = session.execute(select(RuleAuditLogModel)).scalars().all()
        events = session.execute(select(RulePublishedEventModel)).scalars().all()
        assert len(results) >= 1
        assert len(audits) >= 1
        assert len(events) >= 1
        assert events[0].topic == "rule.executed.v1"

    response2 = client.post(
        "/v1/rule/internal/execute",
        json={
            "company_id": "cmp_acme",
            "period_ref": "2026-07-10",
            "orchestrator_run_id": "run_rule_001",
        },
    )

    assert response2.status_code == 200
    payload2 = response2.json()
    assert payload2["idempotent_hits"] >= 1

    app.dependency_overrides.clear()
