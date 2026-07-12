from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

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
    ImportedBalanceSheetFactModel,
    ImportedFinancialFactModel,
    ImportedHrFactModel,
    ImportedIncomeStatementFactModel,
    ImportedInventoryFactModel,
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
            ImportedBalanceSheetFactModel.__table__,
            ImportedIncomeStatementFactModel.__table__,
            ImportedAccountsReceivableFactModel.__table__,
            ImportedAccountsPayableFactModel.__table__,
            ImportedInventoryFactModel.__table__,
            ImportedHrFactModel.__table__,
            ImportPublishedEventModel.__table__,
            CustomerModel.__table__,
            CustomerContactModel.__table__,
            CustomerExternalRefModel.__table__,
            CustomerIngestionRecordModel.__table__,
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


def test_import_customers_csv_persists_customer_and_event() -> None:
    session_factory = _build_session_factory()
    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)

    token = _token(client)
    csv_content = "source_record_id,legal_name,trade_name,document_number,status,billing_street,billing_number,billing_district,billing_city,billing_state,billing_country,billing_postal_code,contact_email,contact_phone,external_id\nSRC-1,ACME LTDA,ACME,12345678000199,active,Rua A,10,Centro,Sao Paulo,SP,Brasil,01000-000,financeiro@acme.com,11999999999,CUST-1\n"

    response = client.post(
        "/v1/imports/csv",
        data={
            "company_id": "cmp_acme",
            "template": "customers",
            "source_system": "csv_manual",
        },
        files={"file": ("customers.csv", csv_content, "text/csv")},
        headers={"Authorization": f"Bearer {token}", "X-Correlation-ID": "imp-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["imported_rows"] == 1

    with session_factory() as session:
        customers = session.execute(select(CustomerModel)).scalars().all()
        events = session.execute(select(ImportPublishedEventModel)).scalars().all()
        assert len(customers) == 1
        assert customers[0].company_id == "cmp_acme"
        assert len(events) == 1
        assert events[0].topic == "ingest.completed.v1"

    app.dependency_overrides.clear()


def test_import_sales_csv_generates_inconsistency_report() -> None:
    session_factory = _build_session_factory()
    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)

    token = _token(client)
    # missing many mandatory columns for the official sales template
    csv_content = "source_record_id,transaction_date\nSRC-1,2026-07-01\n"

    response = client.post(
        "/v1/imports/csv",
        data={
            "company_id": "cmp_acme",
            "template": "sales",
            "source_system": "csv_manual",
        },
        files={"file": ("sales.csv", csv_content, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["failed_rows"] >= 1
    assert len(payload["inconsistencies"]) == 1
    assert payload["inconsistencies"][0]["field"] == "header"

    with session_factory() as session:
        issues = session.execute(select(ImportInconsistencyModel)).scalars().all()
        assert len(issues) == 1

    app.dependency_overrides.clear()


def test_import_endpoint_blocks_tenant_spoofing() -> None:
    session_factory = _build_session_factory()
    app.dependency_overrides[get_db] = _override_db(session_factory)
    client = TestClient(app)

    token = _token(client, company_id="cmp_acme")
    csv_content = "company_id,period_ref,source_record_id,transaction_date,cash_flow_type,account_type,cash_in_amount,cash_out_amount,operating_cash_flow_amount,description\ncmp_acme,2026-07,SRC-1,2026-07-01,operating,bank,1000,200,800,Movimento diario\n"

    response = client.post(
        "/v1/imports/csv",
        data={
            "company_id": "cmp_omega",
            "template": "cashflow",
            "source_system": "csv_manual",
        },
        files={"file": ("cashflow.csv", csv_content, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    app.dependency_overrides.clear()
