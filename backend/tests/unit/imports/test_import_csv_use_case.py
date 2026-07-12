from dataclasses import dataclass

from app.modules.imports.application.contracts import ImportCsvCommand
from app.modules.imports.application.use_cases import ImportCsvUseCase


@dataclass(slots=True)
class _RepoStub:
    inconsistencies: list
    jobs: list
    published: list
    sales: list
    cashflow: list
    balance_sheet: list
    income_statement: list
    accounts_receivable: list
    accounts_payable: list
    inventory: list
    hr: list

    def create_job(self, **kwargs):
        self.jobs.append(kwargs)
        return "imp_1"

    def finish_job(self, **kwargs):
        self.jobs.append(kwargs)

    def add_inconsistency(self, **kwargs):
        self.inconsistencies.append(kwargs["issue"])

    def publish_ingest_completed(self, **kwargs):
        self.published.append(kwargs)

        class _Event:
            event_id = "evt_1"

        return _Event()

    def _insert_unique(self, store: list, payload: dict) -> bool:
        key = (payload["company_id"], payload["source_system"], payload["source_record_id"])
        for item in store:
            old = (item["company_id"], item["source_system"], item["source_record_id"])
            if old == key:
                return False
        store.append(payload)
        return True

    def persist_sale_fact(self, **kwargs) -> bool:
        return self._insert_unique(self.sales, kwargs)

    def persist_financial_fact(self, **kwargs) -> bool:
        return self._insert_unique(self.cashflow, kwargs)

    def persist_balance_sheet_fact(self, **kwargs) -> bool:
        return self._insert_unique(self.balance_sheet, kwargs)

    def persist_income_statement_fact(self, **kwargs) -> bool:
        return self._insert_unique(self.income_statement, kwargs)

    def persist_accounts_receivable_fact(self, **kwargs) -> bool:
        return self._insert_unique(self.accounts_receivable, kwargs)

    def persist_accounts_payable_fact(self, **kwargs) -> bool:
        return self._insert_unique(self.accounts_payable, kwargs)

    def persist_inventory_fact(self, **kwargs) -> bool:
        return self._insert_unique(self.inventory, kwargs)

    def persist_hr_fact(self, **kwargs) -> bool:
        return self._insert_unique(self.hr, kwargs)


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


def _use_case() -> tuple[ImportCsvUseCase, _RepoStub]:
    repo = _RepoStub(
        inconsistencies=[],
        jobs=[],
        published=[],
        sales=[],
        cashflow=[],
        balance_sheet=[],
        income_statement=[],
        accounts_receivable=[],
        accounts_payable=[],
        inventory=[],
        hr=[],
    )
    return ImportCsvUseCase(repository=repo, upsert_customer=_CustomerStub(calls=[]), upsert_product=_ProductStub(calls=[])), repo


def test_import_sales_success() -> None:
    use_case, repo = _use_case()
    csv_content = (
        "company_id,period_ref,source_record_id,transaction_date,invoice_id,invoice_line_id,product_external_id,"
        "customer_external_id,gross_revenue,tax_amount,discount_amount,return_amount,net_revenue,quantity_sold,cogs_amount\n"
        "cmp_acme,2026-07,SRC-S-1,2026-07-01,NF-1,1,PROD-1,CUST-1,1000,100,20,10,870,5,500\n"
    )

    result = use_case.execute(
        ImportCsvCommand(company_id="cmp_acme", template="sales", source_system="csv_manual", csv_content=csv_content)
    )

    assert result.status == "success"
    assert result.imported_rows == 1
    assert len(repo.sales) == 1


def test_import_cashflow_success() -> None:
    use_case, repo = _use_case()
    csv_content = (
        "company_id,period_ref,source_record_id,transaction_date,cash_flow_type,account_type,cash_in_amount,"
        "cash_out_amount,operating_cash_flow_amount,description\n"
        "cmp_acme,2026-07,SRC-CF-1,2026-07-02,operating,bank,1000,200,800,Daily movement\n"
    )

    result = use_case.execute(
        ImportCsvCommand(company_id="cmp_acme", template="cashflow", source_system="csv_manual", csv_content=csv_content)
    )

    assert result.status == "success"
    assert result.imported_rows == 1
    assert len(repo.cashflow) == 1


def test_import_balance_sheet_success() -> None:
    use_case, repo = _use_case()
    csv_content = (
        "company_id,period_ref,reference_date,source_record_id,current_assets,non_current_assets,cash_and_equivalents,"
        "inventory,accounts_receivable,other_current_assets,current_liabilities,non_current_liabilities,accounts_payable,"
        "total_assets,total_liabilities,equity\n"
        "cmp_acme,2026-07,2026-07-31,SRC-BS-1,1000,2000,500,200,300,100,800,600,250,3000,1400,1600\n"
    )

    result = use_case.execute(
        ImportCsvCommand(
            company_id="cmp_acme",
            template="balance_sheet",
            source_system="csv_manual",
            csv_content=csv_content,
        )
    )

    assert result.status == "success"
    assert len(repo.balance_sheet) == 1


def test_import_income_statement_success() -> None:
    use_case, repo = _use_case()
    csv_content = (
        "company_id,period_ref,source_record_id,gross_revenue,net_revenue,cogs,gross_profit,operating_expenses,ebit,"
        "depreciation,amortization,ebitda,financial_income,financial_expense,income_before_tax,income_tax,net_income,nopat\n"
        "cmp_acme,2026-07,SRC-IS-1,5000,4500,2500,2000,800,1200,100,50,1350,20,90,1130,330,800,700\n"
    )

    result = use_case.execute(
        ImportCsvCommand(
            company_id="cmp_acme",
            template="income_statement",
            source_system="csv_manual",
            csv_content=csv_content,
        )
    )

    assert result.status == "success"
    assert len(repo.income_statement) == 1


def test_import_accounts_receivable_success() -> None:
    use_case, repo = _use_case()
    csv_content = (
        "company_id,period_ref,source_record_id,customer_id,invoice_number,issue_date,due_date,payment_date,amount,"
        "received_amount,outstanding_amount,status,aging_days\n"
        "cmp_acme,2026-07,SRC-AR-1,CUST-1,AR-1,2026-07-05,2026-07-20,2026-07-19,1000,1000,0,paid,0\n"
    )

    result = use_case.execute(
        ImportCsvCommand(
            company_id="cmp_acme",
            template="accounts_receivable",
            source_system="csv_manual",
            csv_content=csv_content,
        )
    )

    assert result.status == "success"
    assert len(repo.accounts_receivable) == 1


def test_import_accounts_payable_success() -> None:
    use_case, repo = _use_case()
    csv_content = (
        "company_id,period_ref,source_record_id,supplier_id,invoice_number,issue_date,due_date,payment_date,amount,"
        "paid_amount,outstanding_amount,status,aging_days\n"
        "cmp_acme,2026-07,SRC-AP-1,SUP-1,AP-1,2026-07-03,2026-07-15,2026-07-15,800,800,0,paid,0\n"
    )

    result = use_case.execute(
        ImportCsvCommand(
            company_id="cmp_acme",
            template="accounts_payable",
            source_system="csv_manual",
            csv_content=csv_content,
        )
    )

    assert result.status == "success"
    assert len(repo.accounts_payable) == 1


def test_import_inventory_success() -> None:
    use_case, repo = _use_case()
    csv_content = (
        "company_id,period_ref,source_record_id,product_id,warehouse_id,snapshot_date,opening_quantity,closing_quantity,"
        "average_quantity,average_cost,inventory_value,stock_turnover,days_in_inventory\n"
        "cmp_acme,2026-07,SRC-INV-1,PROD-1,WH-1,2026-07-10,100,90,95,12.5,1187.5,3.2,30\n"
    )

    result = use_case.execute(
        ImportCsvCommand(company_id="cmp_acme", template="inventory", source_system="csv_manual", csv_content=csv_content)
    )

    assert result.status == "success"
    assert len(repo.inventory) == 1


def test_import_hr_success() -> None:
    use_case, repo = _use_case()
    csv_content = (
        "company_id,period_ref,source_record_id,employee_count,active_employee_count,terminated_employee_count,payroll_amount,"
        "average_salary,hours_worked\n"
        "cmp_acme,2026-07,SRC-HR-1,50,48,2,200000,4166.67,8000\n"
    )

    result = use_case.execute(
        ImportCsvCommand(company_id="cmp_acme", template="hr", source_system="csv_manual", csv_content=csv_content)
    )

    assert result.status == "success"
    assert len(repo.hr) == 1


def test_import_partial_when_one_row_invalid() -> None:
    use_case, repo = _use_case()
    csv_content = (
        "company_id,period_ref,source_record_id,transaction_date,invoice_id,invoice_line_id,product_external_id,"
        "customer_external_id,gross_revenue,tax_amount,discount_amount,return_amount,net_revenue,quantity_sold,cogs_amount\n"
        "cmp_acme,2026-07,SRC-S-1,2026-07-01,NF-1,1,PROD-1,CUST-1,1000,100,20,10,870,5,500\n"
        "cmp_acme,2026-07,SRC-S-2,2026-07-01,NF-2,1,PROD-2,CUST-2,-100,10,5,0,85,1,50\n"
    )

    result = use_case.execute(
        ImportCsvCommand(company_id="cmp_acme", template="sales", source_system="csv_manual", csv_content=csv_content)
    )

    assert result.status == "partial"
    assert result.imported_rows == 1
    assert result.failed_rows == 1
    assert len(repo.sales) == 1


def test_import_csv_missing_required_column_fails() -> None:
    use_case, _ = _use_case()
    csv_content = "company_id,period_ref,source_record_id\ncmp_acme,2026-07,SRC-1\n"

    result = use_case.execute(
        ImportCsvCommand(company_id="cmp_acme", template="hr", source_system="csv_manual", csv_content=csv_content)
    )

    assert result.status == "failed"
    assert result.imported_rows == 0
    assert result.inconsistencies[0].field == "header"


def test_import_csv_duplicate_row_in_same_file_fails_duplicate_row() -> None:
    use_case, repo = _use_case()
    csv_content = (
        "company_id,period_ref,source_record_id,employee_count,active_employee_count,terminated_employee_count,payroll_amount,"
        "average_salary,hours_worked\n"
        "cmp_acme,2026-07,SRC-HR-1,50,48,2,200000,4166.67,8000\n"
        "cmp_acme,2026-07,SRC-HR-1,50,48,2,200000,4166.67,8000\n"
    )

    result = use_case.execute(
        ImportCsvCommand(company_id="cmp_acme", template="hr", source_system="csv_manual", csv_content=csv_content)
    )

    assert result.status == "partial"
    assert result.imported_rows == 1
    assert result.failed_rows == 1
    assert len(repo.hr) == 1
    assert any("duplicate row key" in item.message for item in result.inconsistencies)


def test_idempotency_import_does_not_duplicate_records() -> None:
    use_case, repo = _use_case()
    csv_content = (
        "company_id,period_ref,source_record_id,transaction_date,cash_flow_type,account_type,cash_in_amount,"
        "cash_out_amount,operating_cash_flow_amount,description\n"
        "cmp_acme,2026-07,SRC-CF-1,2026-07-02,operating,bank,1000,200,800,Daily movement\n"
    )

    first = use_case.execute(
        ImportCsvCommand(company_id="cmp_acme", template="cashflow", source_system="csv_manual", csv_content=csv_content)
    )
    second = use_case.execute(
        ImportCsvCommand(company_id="cmp_acme", template="cashflow", source_system="csv_manual", csv_content=csv_content)
    )

    assert first.status == "success"
    assert second.status == "success"
    assert len(repo.cashflow) == 1
