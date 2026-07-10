from dataclasses import dataclass

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.dependencies import get_db
from app.main import app
from app.modules.business.application.product_contracts import UpsertProductCommand
from app.modules.business.domain.product_entities import ProductAggregate
from app.modules.business.infrastructure.models import (
    ProductExternalRefModel,
    ProductIngestionRecordModel,
    ProductModel,
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
            ProductModel.__table__,
            ProductExternalRefModel.__table__,
            ProductIngestionRecordModel.__table__,
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


def _token(client: TestClient, company_id: str = "cmp_acme") -> str:
    response = client.post(
        "/v1/auth/login",
        json={
            "email": "owner@acme.com",
            "password": "Owner@123",
            "company_id": company_id,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _payload(company_id: str) -> dict:
    return {
        "company_id": company_id,
        "sku": "PRD-800",
        "name": "Produto 800",
        "category": "CAT-800",
        "unit_of_measure": "UN",
        "status": "active",
        "default_cost": "10",
        "default_price": "20",
        "tax_profile_ref": None,
        "external_refs": [{"source_system": "omie", "external_id": "P-800"}],
        "source_system": "omie",
        "source_record_id": "SRC-800",
        "canonical_schema_version": "1.0.0",
    }


def test_product_tenant_spoofing_is_blocked() -> None:
    session_factory = _build_session_factory()
    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)

    token = _token(client, company_id="cmp_acme")
    response = client.post(
        "/v1/business/products",
        json=_payload(company_id="cmp_omega"),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    app.dependency_overrides.clear()


def test_product_create_all_not_called_in_request_path(monkeypatch) -> None:
    def _raise_if_called(*args, **kwargs):
        raise AssertionError("create_all should not be called in request path")

    session_factory = _build_session_factory()
    monkeypatch.setattr(Base.metadata, "create_all", _raise_if_called)
    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)
    token = _token(client)

    response = client.post(
        "/v1/business/products",
        json=_payload(company_id="cmp_acme"),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    app.dependency_overrides.clear()


def test_product_integrity_error_is_mapped_to_conflict(monkeypatch) -> None:
    import app.modules.business.interfaces.api.product_routes as product_routes

    @dataclass
    class _UpsertStub:
        def execute(self, command: UpsertProductCommand) -> ProductAggregate:
            raise IntegrityError("insert", {}, Exception("duplicate"))

    @dataclass
    class _ContainerStub:
        upsert_product: _UpsertStub

    monkeypatch.setattr(product_routes, "build_product_container", lambda db: _ContainerStub(upsert_product=_UpsertStub()))

    session_factory = _build_session_factory()
    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)
    token = _token(client)

    response = client.post(
        "/v1/business/products",
        json=_payload(company_id="cmp_acme"),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "product conflict detected"
    app.dependency_overrides.clear()
