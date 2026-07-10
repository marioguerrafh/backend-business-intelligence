from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.modules.business.application.product_contracts import GetProductQuery, UpsertProductCommand
from app.modules.business.domain.product_errors import ProductIdempotencyConflictError
from app.modules.business.domain.product_value_objects import ProductExternalReference, ProductStatus
from app.modules.business.infrastructure.models import (
    ProductExternalRefModel,
    ProductIngestionRecordModel,
    ProductModel,
)
from app.modules.business.infrastructure.product_container import build_product_container
from app.shared.infrastructure.db.base import Base


def _session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(
        bind=engine,
        tables=[
            ProductModel.__table__,
            ProductExternalRefModel.__table__,
            ProductIngestionRecordModel.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_upsert_and_get_product_with_sqlalchemy_adapter() -> None:
    session = _session_factory()()
    container = build_product_container(session)

    upsert = container.upsert_product.execute(
        UpsertProductCommand(
            company_id="cmp_acme",
            sku="PRD-100",
            name="Produto 100",
            category="CAT-A",
            unit_of_measure="UN",
            status=ProductStatus.ACTIVE,
            default_cost=Decimal("11"),
            default_price=Decimal("21"),
            tax_profile_ref="TX-1",
            external_refs=(ProductExternalReference(source_system="omie", external_id="P-100"),),
            source_system="omie",
            source_record_id="SRC-100",
            canonical_schema_version="1.0.0",
        )
    )
    session.commit()

    loaded = container.get_product.execute(
        GetProductQuery(company_id="cmp_acme", product_id=upsert.product.product_id)
    )

    assert loaded.product_id == upsert.product.product_id
    assert loaded.sku == "PRD-100"
    assert len(container.publisher.events) == 1


def test_product_idempotency_replay_and_conflict() -> None:
    session = _session_factory()()
    container = build_product_container(session)

    first = container.upsert_product.execute(
        UpsertProductCommand(
            company_id="cmp_acme",
            sku="PRD-500",
            name="Produto 500",
            category="CAT-B",
            unit_of_measure="UN",
            status=ProductStatus.ACTIVE,
            default_cost=Decimal("10"),
            default_price=Decimal("20"),
            tax_profile_ref=None,
            external_refs=(ProductExternalReference(source_system="omie", external_id="P-500"),),
            source_system="omie",
            source_record_id="SRC-500",
            canonical_schema_version="1.0.0",
        )
    )
    session.commit()

    replay = container.upsert_product.execute(
        UpsertProductCommand(
            company_id="cmp_acme",
            sku="PRD-500",
            name="Produto 500",
            category="CAT-B",
            unit_of_measure="UN",
            status=ProductStatus.ACTIVE,
            default_cost=Decimal("10"),
            default_price=Decimal("20"),
            tax_profile_ref=None,
            external_refs=(ProductExternalReference(source_system="omie", external_id="P-500"),),
            source_system="omie",
            source_record_id="SRC-500",
            canonical_schema_version="1.0.0",
        )
    )

    assert replay.idempotent_replay is True
    assert replay.product.product_id == first.product.product_id
    assert replay.event is None
    assert len(container.publisher.events) == 1

    with pytest.raises(ProductIdempotencyConflictError):
        container.upsert_product.execute(
            UpsertProductCommand(
                company_id="cmp_acme",
                sku="PRD-501",
                name="Produto 501",
                category="CAT-C",
                unit_of_measure="UN",
                status=ProductStatus.ACTIVE,
                default_cost=Decimal("15"),
                default_price=Decimal("25"),
                tax_profile_ref=None,
                external_refs=(ProductExternalReference(source_system="omie", external_id="P-501"),),
                source_system="omie",
                source_record_id="SRC-500",
                canonical_schema_version="1.0.0",
            )
        )
