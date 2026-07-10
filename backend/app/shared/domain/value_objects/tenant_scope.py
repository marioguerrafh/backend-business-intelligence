from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TenantScope:
    company_id: str

    def __post_init__(self) -> None:
        if not self.company_id.strip():
            raise ValueError("company_id is required")
