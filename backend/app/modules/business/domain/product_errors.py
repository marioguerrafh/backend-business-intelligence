from app.shared.domain.errors import DomainError


class ProductDomainError(DomainError):
    pass


class InvalidProductStateError(ProductDomainError):
    pass


class DuplicateProductSkuError(ProductDomainError):
    pass


class ProductIdempotencyConflictError(ProductDomainError):
    pass
