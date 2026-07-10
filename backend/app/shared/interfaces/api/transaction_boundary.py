from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.orm import Session

from app.shared.application.transaction.manager import TransactionManager

T = TypeVar("T")


class TransactionBoundary:
    def __init__(self, db: Session) -> None:
        self.manager = TransactionManager(db)

    def execute(self, operation: Callable[[], T]) -> T:
        return self.manager.execute(operation)
