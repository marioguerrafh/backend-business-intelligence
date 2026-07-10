from dataclasses import dataclass
from typing import Callable, Generic, Protocol, TypeVar

EntityT = TypeVar("EntityT")


class IdempotencyRepositoryPort(Protocol):
    def get_idempotency_record(
        self,
        company_id: str,
        source_system: str,
        source_record_id: str,
    ) -> tuple[str, str] | None:
        raise NotImplementedError

    def save_idempotency_record(
        self,
        company_id: str,
        source_system: str,
        source_record_id: str,
        entity_id: str,
        payload_hash: str,
    ) -> None:
        raise NotImplementedError


@dataclass(slots=True, frozen=True)
class IdempotencyContext:
    company_id: str
    source_system: str
    source_record_id: str
    payload_hash: str


@dataclass(slots=True)
class IdempotencyResolution(Generic[EntityT]):
    is_replay: bool
    entity: EntityT | None = None


class IdempotencyService:
    def resolve_replay(
        self,
        context: IdempotencyContext,
        repository: IdempotencyRepositoryPort,
        load_entity: Callable[[str], EntityT | None],
        conflict_error: type[Exception],
        missing_entity_error_message: str,
    ) -> IdempotencyResolution[EntityT]:
        existing = repository.get_idempotency_record(
            company_id=context.company_id,
            source_system=context.source_system,
            source_record_id=context.source_record_id,
        )
        if existing is None:
            return IdempotencyResolution(is_replay=False, entity=None)

        entity_id, saved_payload_hash = existing
        if saved_payload_hash != context.payload_hash:
            raise conflict_error("source record already processed with different payload")

        entity = load_entity(entity_id)
        if entity is None:
            raise conflict_error(missing_entity_error_message)
        return IdempotencyResolution(is_replay=True, entity=entity)

    def persist(
        self,
        context: IdempotencyContext,
        repository: IdempotencyRepositoryPort,
        entity_id: str,
    ) -> None:
        repository.save_idempotency_record(
            context.company_id,
            context.source_system,
            context.source_record_id,
            entity_id,
            context.payload_hash,
        )
