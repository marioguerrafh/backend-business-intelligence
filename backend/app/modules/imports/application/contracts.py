from dataclasses import dataclass
from typing import Literal


ImportTemplate = Literal[
    "customers",
    "products",
    "sales",
    "cashflow",
    "balance_sheet",
    "income_statement",
    "accounts_receivable",
    "accounts_payable",
    "inventory",
    "hr",
    "financial",
]


@dataclass(slots=True, frozen=True)
class ImportCsvCommand:
    company_id: str
    template: ImportTemplate
    source_system: str
    csv_content: str
    canonical_schema_version: str = "1.0.0"
    correlation_id: str | None = None


@dataclass(slots=True, frozen=True)
class ImportInconsistency:
    row_number: int
    field: str
    message: str
    raw_value: str | None = None


@dataclass(slots=True, frozen=True)
class ImportCsvResult:
    job_id: str
    template: ImportTemplate
    status: Literal["success", "partial", "failed"]
    total_rows: int
    imported_rows: int
    failed_rows: int
    inconsistencies: tuple[ImportInconsistency, ...]
    ingest_event_id: str | None
