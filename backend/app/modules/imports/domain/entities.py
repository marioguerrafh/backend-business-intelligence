from dataclasses import dataclass


@dataclass(slots=True)
class importsEntity:
    id: str
    company_id: str
