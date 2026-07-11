from __future__ import annotations

from app.modules.summary.application.ports.repository import SummaryProjectionRecord
from app.modules.summary.domain.entities import SummaryAggregate


class SummaryProjection:
    """Transforms aggregate data into a persisted read model payload."""

    def to_record(self, aggregate: SummaryAggregate) -> SummaryProjectionRecord:
        return SummaryProjectionRecord(
            summary_id=aggregate.summary_id,
            company_id=aggregate.company_id,
            period_ref=aggregate.period_ref,
            payload=aggregate.to_payload(),
            generated_at=aggregate.generated_at,
        )
