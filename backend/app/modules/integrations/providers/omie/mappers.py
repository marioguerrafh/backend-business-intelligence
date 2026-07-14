from __future__ import annotations

from datetime import date
from typing import Any


def map_customer(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "external_id": str(raw.get("codigo_cliente_omie") or raw.get("id") or ""),
        "source_record_id": str(raw.get("codigo_cliente_omie") or raw.get("id") or ""),
        "name": str(raw.get("razao_social") or raw.get("nome_fantasia") or "Cliente Omie"),
        "legal_name": str(raw.get("razao_social") or "Cliente Omie"),
        "trade_name": str(raw.get("nome_fantasia") or raw.get("razao_social") or "Cliente Omie"),
        "document": str(raw.get("cnpj_cpf") or ""),
        "status": "active",
        "email": str(raw.get("email") or ""),
        "phone": str(raw.get("telefone1_ddd") or ""),
    }


def map_product(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "external_id": str(raw.get("codigo_produto") or raw.get("id") or ""),
        "source_record_id": str(raw.get("codigo_produto") or raw.get("id") or ""),
        "sku": str(raw.get("codigo") or raw.get("codigo_produto") or ""),
        "name": str(raw.get("descricao") or "Produto Omie"),
        "category": str(raw.get("ncm") or "Geral"),
        "unit": str(raw.get("unidade") or "UN"),
        "status": "active",
        "default_cost": float(raw.get("valor_custo") or 0.0),
        "default_price": float(raw.get("valor_unitario") or 0.0),
    }


def map_sale(raw: dict[str, Any], *, period_ref: str) -> dict[str, Any]:
    sale_date = str(raw.get("data_emissao") or "2026-07-01")
    return {
        "source_record_id": str(raw.get("codigo_pedido") or raw.get("id") or ""),
        "period_ref": period_ref,
        "transaction_date": date.fromisoformat(sale_date),
        "invoice_id": str(raw.get("numero_pedido") or raw.get("codigo_pedido") or ""),
        "invoice_line_id": "1",
        "product_external_id": str(raw.get("codigo_produto") or "prd-omie"),
        "customer_external_id": str(raw.get("codigo_cliente") or "cli-omie"),
        "gross_revenue": float(raw.get("valor_total_pedido") or 0.0),
        "tax_amount": float(raw.get("valor_impostos") or 0.0),
        "discount_amount": float(raw.get("valor_desconto") or 0.0),
        "return_amount": float(raw.get("valor_devolucao") or 0.0),
        "net_revenue": float(raw.get("valor_liquido") or raw.get("valor_total_pedido") or 0.0),
        "quantity_sold": float(raw.get("quantidade") or 1.0),
        "cogs_amount": float(raw.get("custo_total") or 0.0),
    }


def map_accounts_receivable(raw: dict[str, Any], *, period_ref: str) -> dict[str, Any]:
    issue = date.fromisoformat(str(raw.get("data_emissao") or "2026-07-01"))
    due = date.fromisoformat(str(raw.get("data_vencimento") or "2026-07-30"))
    return {
        "source_record_id": str(raw.get("codigo_lancamento") or raw.get("id") or ""),
        "period_ref": period_ref,
        "customer_id": str(raw.get("codigo_cliente") or "cli-omie"),
        "invoice_number": str(raw.get("numero_documento") or "doc-omie"),
        "issue_date": issue,
        "due_date": due,
        "payment_date": None,
        "amount": float(raw.get("valor_documento") or 0.0),
        "received_amount": float(raw.get("valor_recebido") or 0.0),
        "outstanding_amount": float(raw.get("valor_aberto") or 0.0),
        "status": str(raw.get("status") or "open"),
        "aging_days": int(raw.get("dias_atraso") or 0),
    }


def map_accounts_payable(raw: dict[str, Any], *, period_ref: str) -> dict[str, Any]:
    issue = date.fromisoformat(str(raw.get("data_emissao") or "2026-07-01"))
    due = date.fromisoformat(str(raw.get("data_vencimento") or "2026-07-30"))
    return {
        "source_record_id": str(raw.get("codigo_lancamento") or raw.get("id") or ""),
        "period_ref": period_ref,
        "supplier_id": str(raw.get("codigo_fornecedor") or "for-omie"),
        "invoice_number": str(raw.get("numero_documento") or "doc-omie"),
        "issue_date": issue,
        "due_date": due,
        "payment_date": None,
        "amount": float(raw.get("valor_documento") or 0.0),
        "paid_amount": float(raw.get("valor_pago") or 0.0),
        "outstanding_amount": float(raw.get("valor_aberto") or 0.0),
        "status": str(raw.get("status") or "open"),
        "aging_days": int(raw.get("dias_atraso") or 0),
    }


def map_cashflow(raw: dict[str, Any], *, period_ref: str) -> dict[str, Any]:
    tx_date = date.fromisoformat(str(raw.get("data_lancamento") or "2026-07-01"))
    in_value = float(raw.get("valor_entrada") or 0.0)
    out_value = float(raw.get("valor_saida") or 0.0)
    return {
        "source_record_id": str(raw.get("codigo_lancamento") or raw.get("id") or ""),
        "period_ref": period_ref,
        "transaction_date": tx_date,
        "cash_flow_type": str(raw.get("tipo_fluxo") or "operational"),
        "account_type": str(raw.get("conta") or "default"),
        "cash_in_amount": in_value,
        "cash_out_amount": out_value,
        "operating_cash_flow_amount": in_value - out_value,
        "description": str(raw.get("descricao") or "lancamento omie"),
    }


def map_inventory(raw: dict[str, Any], *, period_ref: str) -> dict[str, Any]:
    snapshot = date.fromisoformat(str(raw.get("data_snapshot") or "2026-07-01"))
    opening = float(raw.get("estoque_inicial") or 0.0)
    closing = float(raw.get("estoque_final") or 0.0)
    avg = (opening + closing) / 2
    avg_cost = float(raw.get("custo_medio") or 0.0)
    return {
        "source_record_id": str(raw.get("codigo_item") or raw.get("id") or ""),
        "period_ref": period_ref,
        "product_id": str(raw.get("codigo_produto") or "prd-omie"),
        "warehouse_id": str(raw.get("codigo_almoxarifado") or "wh-omie"),
        "snapshot_date": snapshot,
        "opening_quantity": opening,
        "closing_quantity": closing,
        "average_quantity": avg,
        "average_cost": avg_cost,
        "inventory_value": closing * avg_cost,
        "stock_turnover": float(raw.get("giro") or 0.0),
        "days_in_inventory": float(raw.get("dias_estoque") or 0.0),
    }


def map_hr(raw: dict[str, Any], *, period_ref: str) -> dict[str, Any]:
    employee_count = int(raw.get("colaboradores_total") or 0)
    active = int(raw.get("colaboradores_ativos") or employee_count)
    terminated = int(raw.get("colaboradores_desligados") or 0)
    payroll = float(raw.get("folha_total") or 0.0)
    avg_salary = payroll / active if active > 0 else 0.0
    return {
        "source_record_id": str(raw.get("codigo_lote") or raw.get("id") or ""),
        "period_ref": period_ref,
        "employee_count": employee_count,
        "active_employee_count": active,
        "terminated_employee_count": terminated,
        "payroll_amount": payroll,
        "average_salary": avg_salary,
        "hours_worked": float(raw.get("horas_trabalhadas") or 0.0),
    }
