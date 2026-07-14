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


def test_integrations_contract_shape() -> None:
    session_factory = _build_session_factory()
    app.dependency_overrides[get_db] = _override_db(session_factory)
    try:
        client = TestClient(app)
        token = _token(client)

        connect_response = client.post(
            "/v1/integrations/connect",
            json={
                "provider": "omie",
                "credentials": {"app_key": "key", "app_secret": "secret", "period_ref": "2026-07"},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert connect_response.status_code == 200
        payload = connect_response.json()
        expected = {
            "id",
            "company_id",
            "provider",
            "status",
            "enabled",
            "last_sync",
            "last_success_sync",
            "created_at",
            "updated_at",
        }
        assert expected.issubset(payload.keys())

        sync_response = client.post(
            f"/v1/integrations/{payload['id']}/sync",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert sync_response.status_code == 200, sync_response.json()
        job_payload = sync_response.json()
        expected_job = {
            "job_id",
            "provider",
            "company_id",
            "status",
            "started_at",
            "finished_at",
            "duration_ms",
            "records_read",
            "records_imported",
            "records_failed",
            "pipeline_run_id",
        }
        assert expected_job.issubset(job_payload.keys())

        health_response = client.get(
            "/v1/integrations/health",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert health_response.status_code == 200
        health_payload = health_response.json()
        assert isinstance(health_payload, list)
        assert len(health_payload) >= 1
        expected_health = {
            "provider",
            "status",
            "last_sync",
            "last_error",
            "avg_latency_ms",
            "queue",
            "circuit_breaker",
            "metrics",
        }
        assert expected_health.issubset(set(health_payload[0].keys()))
    finally:
        app.dependency_overrides.clear()
