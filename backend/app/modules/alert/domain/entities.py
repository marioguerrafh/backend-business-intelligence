from dataclasses import dataclass


@dataclass(slots=True)
class alertEntity:
    id: str
    company_id: str
