from dataclasses import dataclass


@dataclass(slots=True)
class recommendationEntity:
    id: str
    company_id: str
