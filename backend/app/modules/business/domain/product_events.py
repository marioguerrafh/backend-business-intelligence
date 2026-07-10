from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(slots=True, frozen=True)
class BusinessProductUpserted:
    event_id: str
    occurred_at: datetime
    company_id: str
    product_id: str
    source_system: str
    source_record_id: str
    canonical_schema_version: str

    @classmethod
    def create(
        cls,
        company_id: str,
        product_id: str,
        source_system: str,
        source_record_id: str,
        canonical_schema_version: str,
    ) -> "BusinessProductUpserted":
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.now(timezone.utc),
            company_id=company_id,
            product_id=product_id,
            source_system=source_system,
            source_record_id=source_record_id,
            canonical_schema_version=canonical_schema_version,
        )
