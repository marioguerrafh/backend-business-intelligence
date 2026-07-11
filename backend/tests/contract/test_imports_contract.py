from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.dependencies import get_db
from app.main import app
from app.modules.imports.infrastructure.models import (
    ImportedFinancialFactModel,
    ImportedSaleFactModel,
    ImportInconsistencyModel,
    ImportJobModel,
    ImportPublishedEventModel,
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
            ImportJobModel.__table__,
            ImportInconsistencyModel.__table__,
            ImportedSaleFactModel.__table__,
            ImportedFinancialFactModel.__table__,
            ImportPublishedEventModel.__table__,
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


def test_import_csv_contract_shape() -> None:
    session_factory = _build_session_factory()
    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)
    token = _token(client)

    csv_content = "source_record_id,transaction_date,cash_flow_type,account_type,cash_in_amount,cash_out_amount,operating_cash_flow_amount,description\nSRC-1,2026-07-01,operating,bank,1000,200,800,Movimento diario\n"

    response = client.post(
        "/v1/imports/csv",
        data={
            "company_id": "cmp_acme",
            "template": "financial",
            "source_system": "csv_manual",
        },
        files={"file": ("financial.csv", csv_content, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()

    expected = {
        "job_id",
        "template",
        "status",
        "total_rows",
        "imported_rows",
        "failed_rows",
        "ingest_event_id",
        "inconsistencies",
    }
    assert expected.issubset(payload.keys())
    assert payload["template"] == "financial"
    assert isinstance(payload["inconsistencies"], list)

    app.dependency_overrides.clear()
