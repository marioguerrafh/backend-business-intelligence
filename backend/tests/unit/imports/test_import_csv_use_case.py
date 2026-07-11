from dataclasses import dataclass

from app.modules.imports.application.contracts import ImportCsvCommand
from app.modules.imports.application.use_cases import ImportCsvUseCase


@dataclass(slots=True)
class _RepoStub:
    inconsistencies: list
    sale_facts: list
    financial_facts: list
    jobs: list

    def create_job(self, **kwargs):
        self.jobs.append(kwargs)
        return "imp_1"

    def finish_job(self, **kwargs):
        self.jobs.append(kwargs)

    def add_inconsistency(self, **kwargs):
        self.inconsistencies.append(kwargs["issue"])

    def persist_sale_fact(self, **kwargs):
        self.sale_facts.append(kwargs)

    def persist_financial_fact(self, **kwargs):
        self.financial_facts.append(kwargs)

    def publish_ingest_completed(self, **kwargs):
        class _Event:
            event_id = "evt_1"

        return _Event()


@dataclass(slots=True)
class _CustomerStub:
    calls: list

    def execute(self, command):
        self.calls.append(command)


@dataclass(slots=True)
class _ProductStub:
    calls: list

    def execute(self, command):
        self.calls.append(command)


def test_import_customers_csv_success() -> None:
    repo = _RepoStub(inconsistencies=[], sale_facts=[], financial_facts=[], jobs=[])
    customer = _CustomerStub(calls=[])
    product = _ProductStub(calls=[])
    use_case = ImportCsvUseCase(repository=repo, upsert_customer=customer, upsert_product=product)

    csv_content = "source_record_id,legal_name,trade_name,document_number,status,billing_street,billing_number,billing_district,billing_city,billing_state,billing_country,billing_postal_code,contact_email,contact_phone,external_id\nSRC-1,ACME LTDA,ACME,12345678000199,active,Rua A,10,Centro,Sao Paulo,SP,Brasil,01000-000,financeiro@acme.com,11999999999,CUST-1\n"

    result = use_case.execute(
        ImportCsvCommand(
            company_id="cmp_acme",
            template="customers",
            source_system="csv_manual",
            csv_content=csv_content,
        )
    )

    assert result.status == "success"
    assert result.imported_rows == 1
    assert len(customer.calls) == 1


def test_import_sales_invalid_header_generates_inconsistency() -> None:
    repo = _RepoStub(inconsistencies=[], sale_facts=[], financial_facts=[], jobs=[])
    use_case = ImportCsvUseCase(repository=repo, upsert_customer=_CustomerStub(calls=[]), upsert_product=_ProductStub(calls=[]))

    csv_content = "source_record_id,transaction_date\nSRC-1,2026-07-01\n"

    result = use_case.execute(
        ImportCsvCommand(
            company_id="cmp_acme",
            template="sales",
            source_system="csv_manual",
            csv_content=csv_content,
        )
    )

    assert result.status == "failed"
    assert result.imported_rows == 0
    assert len(result.inconsistencies) == 1
    assert result.inconsistencies[0].field == "header"


def test_import_financial_persists_fact() -> None:
    repo = _RepoStub(inconsistencies=[], sale_facts=[], financial_facts=[], jobs=[])
    use_case = ImportCsvUseCase(repository=repo, upsert_customer=_CustomerStub(calls=[]), upsert_product=_ProductStub(calls=[]))

    csv_content = "source_record_id,transaction_date,cash_flow_type,account_type,cash_in_amount,cash_out_amount,operating_cash_flow_amount,description\nSRC-1,2026-07-01,operating,bank,1000,200,800,Movimento diario\n"

    result = use_case.execute(
        ImportCsvCommand(
            company_id="cmp_acme",
            template="financial",
            source_system="csv_manual",
            csv_content=csv_content,
        )
    )

    assert result.status == "success"
    assert result.imported_rows == 1
    assert len(repo.financial_facts) == 1
