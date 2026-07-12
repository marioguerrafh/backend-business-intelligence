# Import Engine v2

Date: 2026-07-12
Status: Approved

## Scope

Import Engine v2 populates all canonical facts required by Canonical Data Model v2 and Formula DSL v2 while keeping existing REST endpoints and event contracts.

Supported templates:
- customers
- products
- sales
- cashflow
- balance_sheet
- income_statement
- accounts_receivable
- accounts_payable
- inventory
- hr

Compatibility alias:
- financial -> cashflow

## Canonical Mapping Coverage

Facts persisted by Import Engine v2:
- fact_sales
- fact_finance_cashflow
- fact_balance_sheet
- fact_income_statement
- fact_accounts_receivable
- fact_accounts_payable
- fact_inventory
- fact_hr

Business master compatibility preserved:
- customers
- products

## Official CSV Templates

Reference demo templates are available in:
- demo/sales.csv
- demo/cashflow.csv
- demo/balance_sheet.csv
- demo/income_statement.csv
- demo/accounts_receivable.csv
- demo/accounts_payable.csv
- demo/inventory.csv
- demo/hr.csv

## Required Columns

sales.csv
- company_id
- period_ref
- source_record_id
- transaction_date
- invoice_id
- invoice_line_id
- product_external_id
- customer_external_id
- gross_revenue
- tax_amount
- discount_amount
- return_amount
- net_revenue
- quantity_sold
- cogs_amount

cashflow.csv
- company_id
- period_ref
- source_record_id
- transaction_date
- cash_flow_type
- account_type
- cash_in_amount
- cash_out_amount
- operating_cash_flow_amount
- description

balance_sheet.csv
- company_id
- period_ref
- reference_date
- source_record_id
- current_assets
- non_current_assets
- cash_and_equivalents
- inventory
- accounts_receivable
- other_current_assets
- current_liabilities
- non_current_liabilities
- accounts_payable
- total_assets
- total_liabilities
- equity

income_statement.csv
- company_id
- period_ref
- source_record_id
- gross_revenue
- net_revenue
- cogs
- gross_profit
- operating_expenses
- ebit
- depreciation
- amortization
- ebitda
- financial_income
- financial_expense
- income_before_tax
- income_tax
- net_income
- nopat

accounts_receivable.csv
- company_id
- period_ref
- source_record_id
- customer_id
- invoice_number
- issue_date
- due_date
- payment_date
- amount
- received_amount
- outstanding_amount
- status
- aging_days

accounts_payable.csv
- company_id
- period_ref
- source_record_id
- supplier_id
- invoice_number
- issue_date
- due_date
- payment_date
- amount
- paid_amount
- outstanding_amount
- status
- aging_days

inventory.csv
- company_id
- period_ref
- source_record_id
- product_id
- warehouse_id
- snapshot_date
- opening_quantity
- closing_quantity
- average_quantity
- average_cost
- inventory_value
- stock_turnover
- days_in_inventory

hr.csv
- company_id
- period_ref
- source_record_id
- employee_count
- active_employee_count
- terminated_employee_count
- payroll_amount
- average_salary
- hours_worked

## Validation Rules

Applied by dedicated mappers:
- Mandatory column validation by template.
- Type conversion for decimal, integer, and date fields.
- ISO date validation.
- Currency/amount validation through decimal parsing.
- company_id consistency between payload and request.
- period_ref format validation (YYYY-MM).
- Key consistency (period_ref aligned with date fields where applicable).
- Negative invalid value checks for non-negative metrics.
- Duplicate rows in the same CSV detected and rejected.

Idempotency strategy:
- Persistence-level deduplication by unique key: company_id + source_system + source_record_id.
- Re-import of the same row does not create duplicates.

## Events and Pipeline Integration

Event contract preserved:
- ingest.completed.v1

Pipeline behavior preserved:
- Pipeline Orchestrator is triggered automatically after ingest.completed.v1 when import status is not failed.

## How To Validate

Run import-focused tests:

```powershell
d:/Projetos/business-intelligence/.venv/Scripts/python.exe -m pytest tests/unit/imports/test_import_csv_use_case.py tests/integration/imports/test_imports_api.py tests/contract/test_imports_contract.py
```

Run full test suite:

```powershell
d:/Projetos/business-intelligence/.venv/Scripts/python.exe -m pytest
```
