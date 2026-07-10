import pytest

from app.shared.application.idempotency.service import IdempotencyContext, IdempotencyService


class ConflictError(Exception):
    pass


class InMemoryRepository:
    def __init__(self) -> None:
        self.record: tuple[str, str] | None = None

    def get_idempotency_record(self, company_id: str, source_system: str, source_record_id: str):
        return self.record

    def save_idempotency_record(
        self,
        company_id: str,
        source_system: str,
        source_record_id: str,
        entity_id: str,
        payload_hash: str,
    ) -> None:
        self.record = (entity_id, payload_hash)


def _context(payload_hash: str = "hash-1") -> IdempotencyContext:
    return IdempotencyContext(
        company_id="cmp",
        source_system="omie",
        source_record_id="SRC-1",
        payload_hash=payload_hash,
    )


def test_resolve_replay_returns_existing_entity() -> None:
    service = IdempotencyService()
    repository = InMemoryRepository()
    repository.record = ("entity-1", "hash-1")

    result = service.resolve_replay(
        context=_context(),
        repository=repository,
        load_entity=lambda entity_id: {"entity_id": entity_id},
        conflict_error=ConflictError,
        missing_entity_error_message="missing",
    )

    assert result.is_replay is True
    assert result.entity == {"entity_id": "entity-1"}


def test_resolve_replay_raises_on_payload_conflict() -> None:
    service = IdempotencyService()
    repository = InMemoryRepository()
    repository.record = ("entity-1", "hash-1")

    with pytest.raises(ConflictError):
        service.resolve_replay(
            context=_context(payload_hash="hash-2"),
            repository=repository,
            load_entity=lambda _: {"entity_id": "entity-1"},
            conflict_error=ConflictError,
            missing_entity_error_message="missing",
        )


def test_persist_saves_idempotency_record() -> None:
    service = IdempotencyService()
    repository = InMemoryRepository()

    service.persist(context=_context(), repository=repository, entity_id="entity-123")

    assert repository.record == ("entity-123", "hash-1")
