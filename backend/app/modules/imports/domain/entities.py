from dataclasses import dataclass
from enum import StrEnum


class ImportTemplateName(StrEnum):
    CUSTOMERS = "customers"
    PRODUCTS = "products"
    SALES = "sales"
    FINANCIAL = "financial"


@dataclass(slots=True, frozen=True)
class CsvRow:
    row_number: int
    data: dict[str, str]
