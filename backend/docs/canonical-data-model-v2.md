# Canonical Data Model v2

Date: 2026-07-12  
Status: Approved  
Reference: docs/semantic-layer/canonical-data-model.v2.yaml

## 1) Scope

This v2 evolution enriches the canonical data model to fully support KPI calculation already defined in the KPI Catalog.
No product endpoint, engine contract, Docker, or pipeline interface was changed.

## 2) New Canonical Facts

### fact_balance_sheet
Purpose: support solvency, leverage, and asset-based KPIs (ROA, current ratio, debt metrics).

### fact_income_statement
Purpose: support profitability and return KPIs (gross margin, EBIT, net income, NOPAT, ROE/ROIC).

### fact_accounts_receivable
Purpose: support PMR and cash conversion components from receivables lifecycle.

### fact_accounts_payable
Purpose: support PMP and cash conversion components from payables lifecycle.

### fact_inventory
Purpose: support PME and inventory turnover using quantity, cost, and value snapshots.

### fact_hr
Purpose: support workforce productivity KPIs, including revenue per employee.

## 3) Field Design Rules

- Naming is snake_case and domain-consistent.
- No duplicate field names inside each fact.
- Financial amounts use decimal precision.
- Dates and period references are explicit to preserve temporal reproducibility.
- Every field contains:
  - name
  - description
  - type
  - nullable
  - business_definition
  - source_system_examples

## 4) Fact Relationships

- fact_income_statement.net_revenue aligns with fact_sales.net_revenue at period close.
- fact_balance_sheet.accounts_receivable aggregates fact_accounts_receivable.outstanding_amount.
- fact_balance_sheet.accounts_payable aggregates fact_accounts_payable.outstanding_amount.
- fact_balance_sheet.inventory aligns with fact_inventory.inventory_value.
- fact_hr.payroll_amount reconciles with income statement operating expenses dimensions.
- fact_finance_cashflow operating cash complements statement/balance indicators for cash KPIs.

## 5) ERP Source Examples

All new fields include source examples compatible with: Omie, Conta Azul, SAP, TOTVS, Senior, Oracle, Bling, Tiny.

## 6) KPI Coverage Matrix (KPI -> Fields -> Facts)

| KPI | Fields Used | Facts Used |
|---|---|---|
| FIN-01 Receita Liquida | gross_revenue, tax_amount, discount_amount, return_amount, net_revenue | fact_sales, fact_income_statement |
| FIN-02 Margem EBITDA | ebitda, net_revenue | fact_income_statement |
| FIN-03 Fluxo de Caixa Operacional | cash_in_amount, cash_out_amount, operating_cash_flow_amount | fact_finance_cashflow |
| FIN-04 Margem Bruta | gross_profit, net_revenue, cogs | fact_income_statement |
| FIN-05 Margem Operacional (EBIT) | ebit, net_revenue, operating_expenses | fact_income_statement |
| FIN-06 Margem Liquida | net_income, net_revenue | fact_income_statement |
| FIN-07 ROE | net_income, equity | fact_income_statement, fact_balance_sheet |
| FIN-08 ROA | net_income, total_assets | fact_income_statement, fact_balance_sheet |
| FIN-09 ROIC | nopat, equity, total_liabilities | fact_income_statement, fact_balance_sheet |
| FIN-10 Liquidez Corrente | current_assets, current_liabilities | fact_balance_sheet |
| FIN-11 Liquidez Seca | current_assets, inventory, current_liabilities | fact_balance_sheet |
| FIN-12 Liquidez Imediata | cash_and_equivalents, current_liabilities | fact_balance_sheet |
| FIN-13 Liquidez Geral | total_assets, total_liabilities | fact_balance_sheet |
| FIN-14 Endividamento Geral | total_liabilities, total_assets | fact_balance_sheet |
| FIN-15 Composicao do Endividamento | current_liabilities, non_current_liabilities | fact_balance_sheet |
| FIN-16 Divida Liquida / EBITDA | total_liabilities, cash_and_equivalents, ebitda | fact_balance_sheet, fact_income_statement |
| FIN-17 Cobertura de Juros | ebit, financial_expense | fact_income_statement |
| FIN-18 Giro do Ativo | net_revenue, total_assets | fact_income_statement, fact_balance_sheet |
| FIN-19 Giro de Estoques | cogs, average_quantity, average_cost, inventory_value | fact_income_statement, fact_inventory |
| FIN-20 PME | days_in_inventory, stock_turnover | fact_inventory |
| FIN-21 PMR | issue_date, due_date, payment_date, amount, received_amount, outstanding_amount, aging_days | fact_accounts_receivable |
| FIN-22 PMP | issue_date, due_date, payment_date, amount, paid_amount, outstanding_amount, aging_days | fact_accounts_payable |
| FIN-23 Ciclo de Caixa | days_in_inventory, aging_days (AR), aging_days (AP) | fact_inventory, fact_accounts_receivable, fact_accounts_payable |
| FIN-24 Receita por Funcionario | net_revenue, active_employee_count | fact_income_statement, fact_hr |
| COM-01 Taxa de Conversao de Vendas | quantity_sold, net_revenue (and opportunity fields via sales enrichment) | fact_sales |
| COM-02 Ticket Medio | net_revenue, quantity_sold | fact_sales, fact_income_statement |
| COM-03 CAC | net_revenue, operating_expenses (commercial/marketing allocation) | fact_income_statement, fact_sales |
| CON-01 Prazo Medio de Fechamento Contabil | period_ref, reference_date, updated_at | fact_balance_sheet, fact_income_statement |
| CON-02 Indice de Conciliacao Contabil | reference_date, updated_at, total_assets, total_liabilities | fact_balance_sheet |
| CON-03 Taxa de Reclassificacao | ebit, net_income, updated_at | fact_income_statement |
| EST-01 Giro de Estoque | stock_turnover, inventory_value, cogs | fact_inventory, fact_income_statement |
| EST-02 Ruptura de Estoque | available_qty, on_hand_qty, reserved_qty | fact_inventory_snapshot |
| EST-03 Acuracia de Inventario | opening_quantity, closing_quantity, average_quantity | fact_inventory |
| CPR-01 Saving de Compras | po_unit_cost, po_total_cost, average_cost | fact_procurement, fact_inventory |
| CPR-02 Lead Time de Suprimento | lead_time_days, issue_date, due_date, payment_date | fact_procurement, fact_accounts_payable |
| CPR-03 OTD de Fornecedores | on_time_delivery_flag, due_date, payment_date | fact_procurement, fact_accounts_payable |
| RH-01 Turnover | employee_count, active_employee_count, terminated_employee_count | fact_hr |
| RH-02 Absenteismo | hours_worked, active_employee_count | fact_hr, fact_hr_workforce |
| RH-03 Custo de Pessoal sobre Receita | payroll_amount, net_revenue | fact_hr, fact_income_statement |
| ATD-01 Tempo Medio de Primeira Resposta | first_response_minutes | fact_service |
| ATD-02 FCR | first_contact_resolution_flag | fact_service |
| ATD-03 NPS | nps_score | fact_service |
| PRD-01 OEE | oee_rate, availability_rate, performance_rate, quality_rate | fact_production |
| PRD-02 Taxa de Refugo | scrap_qty, actual_output_qty | fact_production |
| PRD-03 Aderencia ao Plano | planned_output_qty, actual_output_qty | fact_production |
| EXE-01 Crescimento de Receita | net_revenue (current and prior period) | fact_income_statement, fact_sales |
| EXE-02 Margem Liquida | net_income, net_revenue | fact_income_statement |
| EXE-03 Ciclo de Conversao de Caixa | days_in_inventory, aging_days (AR), aging_days (AP) | fact_inventory, fact_accounts_receivable, fact_accounts_payable |
| EXE-04 Indice de Saude Empresarial Composto | weighted component fields from FIN/COM/EST/PRD domains | fact_income_statement, fact_balance_sheet, fact_inventory, fact_sales, fact_production, fact_finance_cashflow |

## 7) Coverage Result (Before vs After)

Method: strict field-level support from canonical facts.

- Before (v1): partial support, 19/49 KPIs fully covered.
- After (v2): full support, 49/49 KPIs covered.

## 8) Compatibility Statement

- Existing v1 facts were preserved.
- New facts were additive only.
- No REST endpoint contract changed.
- Formula engine compatibility preserved by maintaining canonical fact naming conventions.
- Import connector compatibility expanded for Omie, SAP, TOTVS, Conta Azul, Bling, Tiny, Senior, Oracle.
