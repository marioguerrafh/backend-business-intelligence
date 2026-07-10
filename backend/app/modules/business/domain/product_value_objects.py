from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class ProductStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"


@dataclass(slots=True, frozen=True)
class ProductExternalReference:
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
class ProductPricing:
    default_cost: Decimal
    default_price: Decimal

    def __post_init__(self) -> None:
        if self.default_cost < Decimal("0"):
            raise ValueError("default_cost cannot be negative")
        if self.default_price < Decimal("0"):
            raise ValueError("default_price cannot be negative")


def normalize_sku(sku: str) -> str:
    cleaned = sku.strip().upper()
    if not cleaned:
        raise ValueError("sku is required")
    return cleaned
