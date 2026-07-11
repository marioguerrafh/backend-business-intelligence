from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class GetSummaryQuery:
    company_id: str
    period_ref: str | None = None
    correlation_id: str | None = None
