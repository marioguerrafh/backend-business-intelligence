from fastapi import APIRouter, Depends, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.modules.auth.domain.entities import AuthPrincipal
from app.modules.auth.interfaces.api.dependencies import get_current_principal
from app.modules.business.application.contracts import GetCustomerQuery, UpsertCustomerCommand
from app.modules.business.domain.errors import (
    DuplicateCustomerDocumentError,
    IdempotencyConflictError,
    InvalidCustomerStateError,
)
from app.modules.business.domain.value_objects import (
    BillingAddress,
    ContactChannel,
    ContactChannelType,
    CustomerStatus,
    ExternalReference,
)
from app.modules.business.infrastructure.container import build_customer_container
from app.modules.business.interfaces.api.schemas import CustomerResponse, UpsertCustomerRequest
from app.shared.domain.errors import NotFoundError
from app.shared.interfaces.api.error_mapper import ErrorMapper
from app.shared.interfaces.api.tenant_guard import TenantGuard
from app.shared.interfaces.api.transaction_boundary import TransactionBoundary

router = APIRouter(prefix="/business/customers", tags=["business-customers"])


def _to_response(customer) -> CustomerResponse:
    return CustomerResponse(
        customer_id=customer.customer_id,
        company_id=customer.company_id,
        legal_name=customer.legal_name,
        trade_name=customer.trade_name,
        document_number=customer.document_number,
        status=customer.status.value,
        contacts=[
            {"channel_type": contact.channel_type.value, "value": contact.value}
            for contact in customer.contacts
        ],
        external_refs=[
            {"source_system": external_ref.source_system, "external_id": external_ref.external_id}
            for external_ref in customer.external_refs
        ],
    )


@router.post("", response_model=CustomerResponse)
def upsert_customer(
    payload: UpsertCustomerRequest,
    request: Request,
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> CustomerResponse:
    container = build_customer_container(db)
    tx = TransactionBoundary(db)

    TenantGuard.assert_payload_company(principal.company_id, payload.company_id)

    try:
        result = tx.execute(
            lambda: container.upsert_customer.execute(
                UpsertCustomerCommand(
                    company_id=principal.company_id,
                    legal_name=payload.legal_name,
                    trade_name=payload.trade_name,
                    document_number=payload.document_number,
                    status=CustomerStatus(payload.status),
                    billing_address=BillingAddress(**payload.billing_address.model_dump())
                    if payload.billing_address is not None
                    else None,
                    contacts=tuple(
                        ContactChannel(
                            channel_type=ContactChannelType(contact.channel_type.lower()),
                            value=contact.value,
                        )
                        for contact in payload.contacts
                    ),
                    external_refs=tuple(
                        ExternalReference(
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
    except (InvalidCustomerStateError, DuplicateCustomerDocumentError, IdempotencyConflictError) as exc:
        raise ErrorMapper.conflict(exc) from exc
    except IntegrityError as exc:
        raise ErrorMapper.integrity_conflict("customer conflict detected", exc) from exc

    return _to_response(result.customer)


@router.get("/{company_id}/{customer_id}", response_model=CustomerResponse)
def get_customer(
    company_id: str,
    customer_id: str,
    principal: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> CustomerResponse:
    container = build_customer_container(db)

    TenantGuard.assert_path_company(principal.company_id, company_id)

    try:
        customer = container.get_customer.execute(GetCustomerQuery(company_id=company_id, customer_id=customer_id))
    except NotFoundError as exc:
        raise ErrorMapper.not_found(exc) from exc

    return _to_response(customer)
