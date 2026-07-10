class DomainError(Exception):
    pass


class NotFoundError(DomainError):
    pass


class ForbiddenError(DomainError):
    pass
