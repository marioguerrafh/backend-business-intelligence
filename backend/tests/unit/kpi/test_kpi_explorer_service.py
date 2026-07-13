from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.modules.kpi.application.explorer_service import KpiExplorerService
from app.modules.summary.infrastructure.models import KPIResultModel
from app.shared.infrastructure.db.base import Base


def test_kpi_explorer_service_lists_grouped_kpis() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine, tables=[KPIResultModel.__table__])
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with session_factory() as session:
        session.add(
            KPIResultModel(
                kpi_result_id="k_1",
                company_id="cmp_acme",
                period_ref="2026-07",
                kpi_id="FIN-01",
                kpi_name="Receita Liquida",
                value=1200.0,
                unit="BRL",
                trend="up",
                health="green",
                calculated_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
            )
        )
        session.commit()

        service = KpiExplorerService(session)
        payload = service.list_kpis(company_id="cmp_acme", period_ref="2026-07")

        assert payload["period_ref"] == "2026-07"
        assert len(payload["categories"]) >= 1

        financial = next((item for item in payload["categories"] if item["id"] == "financial"), None)
        assert financial is not None
        fin_item = next((item for item in financial["items"] if item["id"] == "FIN-01"), None)
        assert fin_item is not None
        assert fin_item["formatted_value"].startswith("R$")
        assert fin_item["status"] in {"healthy", "warning", "critical"}
