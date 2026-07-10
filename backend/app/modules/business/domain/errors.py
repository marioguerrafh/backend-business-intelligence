from app.shared.domain.errors import DomainError


class CustomerDomainError(DomainError):
    pass


class InvalidCustomerStateError(CustomerDomainError):
    pass


class DuplicateCustomerDocumentError(CustomerDomainError):
    pass


class TenantMismatchError(CustomerDomainError):
    pass


class IdempotencyConflictError(CustomerDomainError):
    pass
