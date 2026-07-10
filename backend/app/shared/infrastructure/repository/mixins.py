from sqlalchemy import select


class SqlAlchemyIdempotencyMixin:
    session: object

    def _get_idempotency_record(
        self,
        model_cls,
        company_id: str,
        source_system: str,
        source_record_id: str,
        entity_id_field: str,
    ) -> tuple[str, str] | None:
        stmt = select(model_cls).where(
            model_cls.company_id == company_id,
            model_cls.source_system == source_system.lower(),
            model_cls.source_record_id == source_record_id,
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return getattr(model, entity_id_field), model.payload_hash

    def _save_idempotency_record(
        self,
        model_cls,
        company_id: str,
        source_system: str,
        source_record_id: str,
        entity_id: str,
        payload_hash: str,
        entity_id_field: str,
        id_field: str,
        id_factory,
    ) -> None:
        stmt = select(model_cls).where(
            model_cls.company_id == company_id,
            model_cls.source_system == source_system.lower(),
            model_cls.source_record_id == source_record_id,
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        if model is None:
            data = {
                id_field: id_factory(),
                "company_id": company_id,
                "source_system": source_system.lower(),
                "source_record_id": source_record_id,
                entity_id_field: entity_id,
                "payload_hash": payload_hash,
            }
            self.session.add(model_cls(**data))
            return

        setattr(model, entity_id_field, entity_id)
        model.payload_hash = payload_hash
