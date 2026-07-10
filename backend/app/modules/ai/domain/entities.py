from dataclasses import dataclass


@dataclass(slots=True)
class aiEntity:
    id: str
    company_id: str
