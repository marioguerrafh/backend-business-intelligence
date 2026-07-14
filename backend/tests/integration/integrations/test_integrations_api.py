from fastapi.testclient import TestClient
from datetime import datetime, timezone
from sqlalchemy import Table, create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from typing import cast

from app.config.dependencies import get_db
from app.main import app
from app.modules.business.infrastructure.models import (
    CustomerContactModel,
    CustomerExternalRefModel,
    CustomerIngestionRecordModel,
    CustomerModel,
    ProductExternalRefModel,
    ProductIngestionRecordModel,
    ProductModel,
)
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
from app.modules.integrations.providers.omie.provider import OmieProvider
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
            CustomerContactModel.__table__,
            CustomerExternalRefModel.__table__,
            CustomerIngestionRecordModel.__table__,
            ProductModel.__table__,
            ProductExternalRefModel.__table__,
            ProductIngestionRecordModel.__table__,
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

    health_response = client.get("/v1/integrations/health", headers={"Authorization": f"Bearer {token}"})
    assert health_response.status_code == 200
    assert len(health_response.json()) == 1
    assert health_response.json()[0]["provider"] == "omie"

    delete_response = client.delete(f"/v1/integrations/{integration_id}", headers={"Authorization": f"Bearer {token}"})
    assert delete_response.status_code == 200

    app.dependency_overrides.clear()


def test_full_sync_deduplicates_customers_with_same_document() -> None:
    session_factory = _build_session_factory()
    app.dependency_overrides[get_db] = _override_db(session_factory)

    original_mock_payload = OmieProvider._mock_payload

    def _mock_payload_with_duplicate_customer(*, endpoint: str, mode: str) -> list[dict[str, object]]:
        if endpoint == "customers":
            return [
                {
                    "codigo_cliente_omie": "CLI-OMIE-1",
                    "razao_social": "Cliente Um",
                    "nome_fantasia": "Cliente Um",
                    "cnpj_cpf": "176.400.928-25",
                    "email": "um@acme.com",
                },
                {
                    "codigo_cliente_omie": "CLI-OMIE-2",
                    "razao_social": "Cliente Dois",
                    "nome_fantasia": "Cliente Dois",
                    "cnpj_cpf": "17640092825",
                    "email": "dois@acme.com",
                },
            ]
        return original_mock_payload(endpoint=endpoint, mode=mode)

    OmieProvider._mock_payload = staticmethod(_mock_payload_with_duplicate_customer)

    try:
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
                    "correlation_id": "int-test-dup-doc",
                },
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert connect_response.status_code == 200
        integration_id = connect_response.json()["id"]

        sync_response = client.post(
            f"/v1/integrations/{integration_id}/full-sync",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert sync_response.status_code == 200
        job_id = sync_response.json()["job_id"]

        job_response = client.get(f"/v1/integrations/jobs/{job_id}", headers={"Authorization": f"Bearer {token}"})
        assert job_response.status_code == 200
        assert job_response.json()["status"] == "success"

        db: Session = session_factory()
        try:
            customer_count = db.execute(select(CustomerModel).where(CustomerModel.company_id == "cmp_acme")).scalars().all()
            assert len(customer_count) == 1
            assert customer_count[0].document_number == "17640092825"
        finally:
            db.close()
    finally:
        OmieProvider._mock_payload = staticmethod(original_mock_payload)
        app.dependency_overrides.clear()


def test_full_sync_rejects_when_running_job_exists() -> None:
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
                "correlation_id": "int-test-running-job",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert connect_response.status_code == 200
    integration_id = connect_response.json()["id"]

    db: Session = session_factory()
    try:
        db.add(
            IntegrationSyncJobModel(
                job_id="isj_running_guard",
                provider="omie",
                company_id="cmp_acme",
                status="running",
                started_at=datetime.now(timezone.utc),
                finished_at=None,
                duration_ms=None,
                records_read=0,
                records_imported=0,
                records_failed=0,
                pipeline_run_id=None,
            )
        )
        db.commit()
    finally:
        db.close()

    sync_response = client.post(
        f"/v1/integrations/{integration_id}/full-sync",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sync_response.status_code == 422
    assert "already running" in str(sync_response.json().get("detail", "")).lower()

    app.dependency_overrides.clear()
