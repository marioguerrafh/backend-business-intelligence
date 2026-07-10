import pytest

from app.shared.application.transaction.manager import TransactionManager


class FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_transaction_manager_commits_on_success() -> None:
    session = FakeSession()
    manager = TransactionManager(session)  # type: ignore[arg-type]

    result = manager.execute(lambda: 42)

    assert result == 42
    assert session.committed is True
    assert session.rolled_back is False


def test_transaction_manager_rolls_back_on_error() -> None:
    session = FakeSession()
    manager = TransactionManager(session)  # type: ignore[arg-type]

    with pytest.raises(RuntimeError):
        manager.execute(lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    assert session.committed is False
    assert session.rolled_back is True
