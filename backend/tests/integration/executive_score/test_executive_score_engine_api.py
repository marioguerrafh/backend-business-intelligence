from datetime import datetime, timezone
from typing import cast

from fastapi.testclient import TestClient
from sqlalchemy import Table, create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.dependencies import get_db
from app.main import app
from app.modules.executive_score.infrastructure.models import ExecutiveScoreAuditLogModel, ExecutiveScorePublishedEventModel
from app.modules.rule.infrastructure.models import RuleResultModel
from app.modules.summary.infrastructure.models import ExecutiveScoreModel, KPIResultModel, RecommendationResultModel, TimelineSnapshotModel
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
            ExecutiveScoreModel.__table__,
            TimelineSnapshotModel.__table__,
            ExecutiveScoreAuditLogModel.__table__,
            ExecutiveScorePublishedEventModel.__table__,
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
        session.add_all(
            [
                KPIResultModel(
                    kpi_result_id="k_fin",
                    company_id="cmp_acme",
                    period_ref="2026-07",
                    period_grain="month",
                    kpi_id="FIN-01",
                    formula_id="f.fin01",
                    kpi_name="finance",
                    value=82.0,
                    unit="score",
                    confidence_score=1.0,
                    trend="up",
                    health="green",
                    orchestrator_run_id="run_kpi",
                    calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                ),
                KPIResultModel(
                    kpi_result_id="k_com",
                    company_id="cmp_acme",
                    period_ref="2026-07",
                    period_grain="month",
                    kpi_id="COM-01",
                    formula_id="f.com01",
                    kpi_name="commercial",
                    value=75.0,
                    unit="score",
                    confidence_score=1.0,
                    trend="up",
                    health="green",
                    orchestrator_run_id="run_kpi",
                    calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                ),
                KPIResultModel(
                    kpi_result_id="k_opr",
                    company_id="cmp_acme",
                    period_ref="2026-07",
                    period_grain="month",
                    kpi_id="OPR-01",
                    formula_id="f.opr01",
                    kpi_name="operational",
                    value=70.0,
                    unit="score",
                    confidence_score=1.0,
                    trend="up",
                    health="green",
                    orchestrator_run_id="run_kpi",
                    calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                ),
                KPIResultModel(
                    kpi_result_id="k_est",
                    company_id="cmp_acme",
                    period_ref="2026-07",
                    period_grain="month",
                    kpi_id="EST-02",
                    formula_id="f.est02",
                    kpi_name="inventory",
                    value=65.0,
                    unit="score",
                    confidence_score=1.0,
                    trend="down",
                    health="yellow",
                    orchestrator_run_id="run_kpi",
                    calculated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                ),
            ]
        )
        session.add(
            RuleResultModel(
                rule_result_id="rr_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                kpi_id="EST-02",
                rule_id="r.est02.stockout_over_5",
                severity="MEDIUM",
                priority="p1",
                alert_title="ruptura",
                alert_description="desc",
                metric_value=7.0,
                fired_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
                orchestrator_run_id="run_rule_1",
            )
        )
        session.add(
            RecommendationResultModel(
                recommendation_result_id="rec_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                recommendation_id="rec.stockout.001",
                title="reposicao_urgente_sku_critico",
                rank_score=0.9,
                expected_impact_json={"value": 5000, "unit": "BRL"},
                owner_role="supply_chain_manager",
                sla_target="12h",
                generated_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            )
        )
        session.commit()


def test_executive_score_internal_api_calculates_and_publishes() -> None:
    session_factory = _build_session_factory()
    _seed(session_factory)
    app.dependency_overrides[get_db] = _override_db(session_factory)

    client = TestClient(app)
    response = client.post(
        "/v1/executive-score/internal/calculate",
        json={
            "company_id": "cmp_acme",
            "period_ref": "2026-07",
            "orchestrator_run_id": "run_exec_1",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert 0 <= payload["executive_score"] <= 100

    with session_factory() as session:
        scores = session.execute(select(ExecutiveScoreModel)).scalars().all()
        timelines = session.execute(select(TimelineSnapshotModel)).scalars().all()
        audits = session.execute(select(ExecutiveScoreAuditLogModel)).scalars().all()
        events = session.execute(select(ExecutiveScorePublishedEventModel)).scalars().all()

        assert len(scores) == 1
        assert len(timelines) == 1
        assert len(audits) == 1
        assert len(events) == 1
        assert events[0].topic == "executive.score.updated.v1"

    app.dependency_overrides.clear()
