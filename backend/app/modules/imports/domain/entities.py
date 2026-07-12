from dataclasses import dataclass
from enum import StrEnum


class ImportTemplateName(StrEnum):
    CUSTOMERS = "customers"
    PRODUCTS = "products"
    SALES = "sales"
    CASHFLOW = "cashflow"
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    ACCOUNTS_PAYABLE = "accounts_payable"
    INVENTORY = "inventory"
    HR = "hr"
    FINANCIAL = "financial"


@dataclass(slots=True, frozen=True)
class CsvRow:
    row_number: int
    data: dict[str, str]
