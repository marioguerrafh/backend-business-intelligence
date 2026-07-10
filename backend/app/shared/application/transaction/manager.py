from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class TransactionManager:
    def __init__(self, session: Session) -> None:
        self.session = session

    def execute(self, operation: Callable[[], T]) -> T:
        try:
            result = operation()
            self.session.commit()
            return result
        except Exception:
            self.session.rollback()
            raise
