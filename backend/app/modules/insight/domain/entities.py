from dataclasses import dataclass


@dataclass(slots=True)
class insightEntity:
    id: str
    company_id: str
