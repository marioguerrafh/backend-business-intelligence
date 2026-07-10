from dataclasses import dataclass
from enum import StrEnum


class CustomerStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class ContactChannelType(StrEnum):
    EMAIL = "email"
    PHONE = "phone"
    WHATSAPP = "whatsapp"


@dataclass(slots=True, frozen=True)
class ExternalReference:
    source_system: str
    external_id: str

    def __post_init__(self) -> None:
        source = self.source_system.strip().lower()
        external = self.external_id.strip()
        if not source:
            raise ValueError("source_system is required")
        if not external:
            raise ValueError("external_id is required")
        object.__setattr__(self, "source_system", source)
        object.__setattr__(self, "external_id", external)


@dataclass(slots=True, frozen=True)
class BillingAddress:
    street: str
    number: str | None
    district: str | None
    city: str
    state: str
    country: str
    postal_code: str | None

    def __post_init__(self) -> None:
        if not self.street.strip():
            raise ValueError("street is required")
        if not self.city.strip():
            raise ValueError("city is required")
        if not self.state.strip():
            raise ValueError("state is required")
        if not self.country.strip():
            raise ValueError("country is required")


@dataclass(slots=True, frozen=True)
class ContactChannel:
    channel_type: ContactChannelType
    value: str

    def __post_init__(self) -> None:
        content = self.value.strip()
        if not content:
            raise ValueError("contact value is required")
        object.__setattr__(self, "value", content)


def normalize_document_number(document_number: str | None) -> str | None:
    if document_number is None:
        return None
    normalized = "".join(character for character in document_number if character.isdigit())
    return normalized or None
