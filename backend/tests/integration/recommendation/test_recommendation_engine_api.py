from datetime import datetime, timezone
from typing import cast

from fastapi.testclient import TestClient
from sqlalchemy import Table, create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.dependencies import get_db
from app.main import app
from app.modules.recommendation.infrastructure.models import RecommendationAuditLogModel, RecommendationPublishedEventModel
from app.modules.rule.infrastructure.models import RuleResultModel
from app.modules.summary.infrastructure.models import KPIResultModel, RecommendationResultModel
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
            RecommendationAuditLogModel.__table__,
            RecommendationPublishedEventModel.__table__,
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


def _seed(session_factory) -> None:
    with session_factory() as session:
        session.add(
            KPIResultModel(
                kpi_result_id="kpi_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                period_grain="month",
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
            RuleResultModel(
                rule_result_id="rr_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                kpi_id="FIN-03",
                rule_id="r.fin03.cash_negative_3d",
                severity="HIGH",
                priority="p0",
                alert_title="fluxo_caixa_negativo_tres_dias",
                alert_description="desc",
                metric_value=-1200.0,
                fired_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                orchestrator_run_id="run_rule_1",
            )
        )
        session.commit()


def test_recommendation_internal_api_generates_and_publishes() -> None:
    session_factory = _build_session_factory()
    _seed(session_factory)
    app.dependency_overrides[get_db] = _override_db(session_factory)

    client = TestClient(app)
    response = client.post(
        "/v1/recommendation/internal/generate",
        json={
            "company_id": "cmp_acme",
            "period_ref": "2026-07",
            "orchestrator_run_id": "run_rec_1",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["generated_count"] >= 1

    with session_factory() as session:
        recs = session.execute(select(RecommendationResultModel)).scalars().all()
        audits = session.execute(select(RecommendationAuditLogModel)).scalars().all()
        events = session.execute(select(RecommendationPublishedEventModel)).scalars().all()
        assert len(recs) >= 1
        assert len(audits) >= 1
        assert len(events) >= 1
        assert events[0].topic == "recommendation.generated.v1"

    app.dependency_overrides.clear()
