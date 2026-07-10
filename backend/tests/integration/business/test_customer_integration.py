import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.modules.business.application.contracts import GetCustomerQuery, UpsertCustomerCommand
from app.modules.business.domain.errors import IdempotencyConflictError
from app.modules.business.domain.value_objects import ContactChannel, ContactChannelType, CustomerStatus, ExternalReference
from app.modules.business.infrastructure.container import build_customer_container
from app.modules.business.infrastructure.models import (
    CustomerContactModel,
    CustomerExternalRefModel,
    CustomerIngestionRecordModel,
    CustomerModel,
)
from app.shared.infrastructure.db.base import Base


def _session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(
        bind=engine,
        tables=[
            CustomerModel.__table__,
            CustomerContactModel.__table__,
            CustomerExternalRefModel.__table__,
            CustomerIngestionRecordModel.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_upsert_and_get_customer_with_sqlalchemy_adapter() -> None:
    session = _session_factory()()
    container = build_customer_container(session)

    upsert = container.upsert_customer.execute(
        UpsertCustomerCommand(
            company_id="cmp_acme",
            legal_name="ACME LTDA",
            trade_name="ACME",
            document_number="12.345.678/0001-99",
            status=CustomerStatus.ACTIVE,
            billing_address=None,
            contacts=(ContactChannel(channel_type=ContactChannelType.EMAIL, value="financeiro@acme.com"),),
            external_refs=(ExternalReference(source_system="omie", external_id="CUST-100"),),
            source_system="omie",
            source_record_id="CUST-100",
            canonical_schema_version="1.0.0",
        )
    )
    session.commit()

    loaded = container.get_customer.execute(
        GetCustomerQuery(company_id="cmp_acme", customer_id=upsert.customer.customer_id)
    )

    assert loaded.customer_id == upsert.customer.customer_id
    assert loaded.document_number == "12345678000199"
    assert len(container.publisher.events) == 1


def test_upsert_customer_idempotency_replay_and_conflict() -> None:
    session = _session_factory()()
    container = build_customer_container(session)

    first = container.upsert_customer.execute(
        UpsertCustomerCommand(
            company_id="cmp_acme",
            legal_name="ACME LTDA",
            trade_name="ACME",
            document_number="12.345.678/0001-99",
            status=CustomerStatus.ACTIVE,
            billing_address=None,
            contacts=(ContactChannel(channel_type=ContactChannelType.EMAIL, value="financeiro@acme.com"),),
            external_refs=(ExternalReference(source_system="omie", external_id="CUST-500"),),
            source_system="omie",
            source_record_id="SRC-500",
            canonical_schema_version="1.0.0",
        )
    )
    session.commit()

    replay = container.upsert_customer.execute(
        UpsertCustomerCommand(
            company_id="cmp_acme",
            legal_name="ACME LTDA",
            trade_name="ACME",
            document_number="12.345.678/0001-99",
            status=CustomerStatus.ACTIVE,
            billing_address=None,
            contacts=(ContactChannel(channel_type=ContactChannelType.EMAIL, value="financeiro@acme.com"),),
            external_refs=(ExternalReference(source_system="omie", external_id="CUST-500"),),
            source_system="omie",
            source_record_id="SRC-500",
            canonical_schema_version="1.0.0",
        )
    )

    assert replay.idempotent_replay is True
    assert replay.customer.customer_id == first.customer.customer_id
    assert replay.event is None
    assert len(container.publisher.events) == 1

    with pytest.raises(IdempotencyConflictError):
        container.upsert_customer.execute(
            UpsertCustomerCommand(
                company_id="cmp_acme",
                legal_name="ACME CHANGED",
                trade_name="ACME",
                document_number="98.765.432/0001-10",
                status=CustomerStatus.ACTIVE,
                billing_address=None,
                contacts=(ContactChannel(channel_type=ContactChannelType.EMAIL, value="financeiro@acme.com"),),
                external_refs=(ExternalReference(source_system="omie", external_id="CUST-501"),),
                source_system="omie",
                source_record_id="SRC-500",
                canonical_schema_version="1.0.0",
            )
        )
