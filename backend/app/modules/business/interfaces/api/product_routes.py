from fastapi import APIRouter, Depends, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.auth.domain.entities import AuthPrincipal
from app.modules.auth.interfaces.api.dependencies import get_current_principal
from app.modules.business.application.product_contracts import GetProductQuery, UpsertProductCommand
from app.modules.business.domain.product_errors import (
    DuplicateProductSkuError,
    InvalidProductStateError,
    ProductIdempotencyConflictError,
)
from app.modules.business.domain.product_value_objects import ProductExternalReference, ProductStatus
from app.modules.business.infrastructure.product_container import build_product_container
from app.modules.business.interfaces.api.product_schemas import ProductResponse, UpsertProductRequest
from app.shared.domain.errors import NotFoundError
from app.shared.interfaces.api.error_mapper import ErrorMapper
from app.shared.interfaces.api.tenant_guard import TenantGuard
from app.shared.interfaces.api.transaction_boundary import TransactionBoundary

router = APIRouter(prefix="/business/products", tags=["business-products"])


def _to_response(product) -> ProductResponse:
    return ProductResponse(
        product_id=product.product_id,
        company_id=product.company_id,
        sku=product.sku,
        name=product.name,
        category=product.category,
        unit_of_measure=product.unit_of_measure,
        status=product.status.value,
        default_cost=str(product.pricing.default_cost),
        default_price=str(product.pricing.default_price),
        tax_profile_ref=product.tax_profile_ref,
        external_refs=[
            {"source_system": external_ref.source_system, "external_id": external_ref.external_id}
            for external_ref in product.external_refs
        ],
    )


@router.post("", response_model=ProductResponse)
def upsert_product(
    payload: UpsertProductRequest,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> ProductResponse:
    container = build_product_container(db)
    tx = TransactionBoundary(db)

    TenantGuard.assert_payload_company(principal.company_id, payload.company_id)

    try:
        result = tx.execute(
            lambda: container.upsert_product.execute(
                UpsertProductCommand(
                    company_id=principal.company_id,
                    sku=payload.sku,
                    name=payload.name,
                    category=payload.category,
                    unit_of_measure=payload.unit_of_measure,
                    status=ProductStatus(payload.status),
                    default_cost=payload.default_cost,
                    default_price=payload.default_price,
                    tax_profile_ref=payload.tax_profile_ref,
                    external_refs=tuple(
                        ProductExternalReference(
                            source_system=external_ref.source_system,
                            external_id=external_ref.external_id,
                        )
                        for external_ref in payload.external_refs
                    ),
                    source_system=payload.source_system,
                    source_record_id=payload.source_record_id,
                    canonical_schema_version=payload.canonical_schema_version,
                    correlation_id=request.headers.get("X-Correlation-ID"),
                )
            )
        )
    except ValueError as exc:
        raise ErrorMapper.unprocessable(exc) from exc
    except (InvalidProductStateError, DuplicateProductSkuError, ProductIdempotencyConflictError) as exc:
        raise ErrorMapper.conflict(exc) from exc
    except IntegrityError as exc:
        raise ErrorMapper.integrity_conflict("product conflict detected", exc) from exc

    return _to_response(result.product)


@router.get("/{company_id}/{product_id}", response_model=ProductResponse)
def get_product(
    company_id: str,
    product_id: str,
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> ProductResponse:
    container = build_product_container(db)

    TenantGuard.assert_path_company(principal.company_id, company_id)

    try:
        product = container.get_product.execute(GetProductQuery(company_id=company_id, product_id=product_id))
    except NotFoundError as exc:
        raise ErrorMapper.not_found(exc) from exc

    return _to_response(product)
