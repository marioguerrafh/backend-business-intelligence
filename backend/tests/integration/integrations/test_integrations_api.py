from fastapi.testclient import TestClient
from sqlalchemy import Table, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from typing import cast

from app.config.dependencies import get_db
from app.main import app
from app.modules.business.infrastructure.models import CustomerModel, ProductModel
from app.modules.imports.infrastructure.models import (
    ImportedAccountsPayableFactModel,
    ImportedAccountsReceivableFactModel,
    ImportedFinancialFactModel,
    ImportedHrFactModel,
    ImportedInventoryFactModel,
    ImportedSaleFactModel,
    ImportInconsistencyModel,
    ImportJobModel,
    ImportPublishedEventModel,
)
from app.modules.integrations.infrastructure.models import (
    IntegrationConnectionModel,
    IntegrationLogModel,
    IntegrationPublishedEventModel,
    IntegrationSyncJobModel,
)
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
            IntegrationConnectionModel.__table__,
            IntegrationSyncJobModel.__table__,
            IntegrationLogModel.__table__,
            IntegrationPublishedEventModel.__table__,
            ImportJobModel.__table__,
            ImportInconsistencyModel.__table__,
            ImportPublishedEventModel.__table__,
            ImportedSaleFactModel.__table__,
            ImportedFinancialFactModel.__table__,
            ImportedAccountsReceivableFactModel.__table__,
            ImportedAccountsPayableFactModel.__table__,
            ImportedInventoryFactModel.__table__,
            ImportedHrFactModel.__table__,
            CustomerModel.__table__,
            ProductModel.__table__,
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


def _token(client: TestClient) -> str:
    response = client.post(
        "/v1/auth/login",
        json={"email": "owner@acme.com", "password": "Owner@123", "company_id": "cmp_acme"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_connect_sync_and_disconnect_integration() -> None:
    session_factory = _build_session_factory()
    app.dependency_overrides[get_db] = _override_db(session_factory)

    client = TestClient(app)
    token = _token(client)

    connect_response = client.post(
        "/v1/integrations/connect",
        json={
            "provider": "omie",
            "credentials": {
                "app_key": "key",
                "app_secret": "secret",
                "period_ref": "2026-07",
                "correlation_id": "int-test-1",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert connect_response.status_code == 200
    integration_id = connect_response.json()["id"]

    list_response = client.get("/v1/integrations", headers={"Authorization": f"Bearer {token}"})
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    sync_response = client.post(
        f"/v1/integrations/{integration_id}/full-sync",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sync_response.status_code == 200
    job_id = sync_response.json()["job_id"]

    job_response = client.get(f"/v1/integrations/jobs/{job_id}", headers={"Authorization": f"Bearer {token}"})
    assert job_response.status_code == 200
    assert job_response.json()["status"] in {"success", "failed"}

    delete_response = client.delete(f"/v1/integrations/{integration_id}", headers={"Authorization": f"Bearer {token}"})
    assert delete_response.status_code == 200

    app.dependency_overrides.clear()
