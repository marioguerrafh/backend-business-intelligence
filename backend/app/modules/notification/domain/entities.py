from dataclasses import dataclass


@dataclass(slots=True)
class notificationEntity:
    id: str
    company_id: str
