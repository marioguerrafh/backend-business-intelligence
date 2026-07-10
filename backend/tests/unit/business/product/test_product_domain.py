from decimal import Decimal

import pytest

from app.modules.business.domain.product_entities import ProductAggregate
from app.modules.business.domain.product_errors import InvalidProductStateError
from app.modules.business.domain.product_value_objects import ProductExternalReference, ProductStatus


def test_product_requires_sku() -> None:
    with pytest.raises(ValueError):
        ProductAggregate.create(
            company_id="cmp_acme",
            sku="   ",
            name="Produto A",
            category="Categoria",
            unit_of_measure="UN",
            status=ProductStatus.ACTIVE,
            default_cost=Decimal("10"),
            default_price=Decimal("15"),
            tax_profile_ref=None,
            external_refs=(ProductExternalReference(source_system="omie", external_id="PRD-1"),),
        )


def test_product_rejects_negative_price() -> None:
    with pytest.raises(ValueError):
        ProductAggregate.create(
            company_id="cmp_acme",
            sku="prd-001",
            name="Produto A",
            category="Categoria",
            unit_of_measure="UN",
            status=ProductStatus.ACTIVE,
            default_cost=Decimal("10"),
            default_price=Decimal("-1"),
            tax_profile_ref=None,
            external_refs=(ProductExternalReference(source_system="omie", external_id="PRD-1"),),
        )


def test_product_normalizes_sku() -> None:
    product = ProductAggregate.create(
        company_id="cmp_acme",
        sku=" prd-001 ",
        name="Produto A",
        category="Categoria",
        unit_of_measure="un",
        status=ProductStatus.ACTIVE,
        default_cost=Decimal("10"),
        default_price=Decimal("20"),
        tax_profile_ref=None,
        external_refs=(ProductExternalReference(source_system="omie", external_id="PRD-1"),),
    )

    assert product.sku == "PRD-001"
    assert product.unit_of_measure == "UN"
