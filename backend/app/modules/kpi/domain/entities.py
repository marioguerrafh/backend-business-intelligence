from dataclasses import dataclass


@dataclass(slots=True)
class kpiEntity:
    id: str
    company_id: str
