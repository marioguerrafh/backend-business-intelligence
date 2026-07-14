from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any


def _pick(raw: dict[str, Any], *paths: str) -> Any:
    for path in paths:
        current: Any = raw
        found = True
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                found = False
                break
        if not found:
            continue
        if current is None:
            continue
        if isinstance(current, str) and not current.strip():
            continue
        return current
    return None


def _to_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _raw_str(raw: dict[str, Any], *paths: str, default: str = "") -> str:
    return _to_str(_pick(raw, *paths), default)


def _to_number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)

    text = _to_str(value)
    if not text:
        return default

    text = text.replace(" ", "")
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return default


def _raw_float(raw: dict[str, Any], *paths: str, default: float = 0.0) -> float:
    return _to_number(_pick(raw, *paths), default)


def _raw_int(raw: dict[str, Any], *paths: str, default: int = 0) -> int:
    return int(_to_number(_pick(raw, *paths), float(default)))


def _parse_date(value: Any, default: date) -> date:
    if isinstance(value, date):
        return value

    text = _to_str(value)
    if not text:
        return default

    if "T" in text:
        text = text.split("T", 1)[0]

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    try:
        return date.fromisoformat(text)
    except ValueError:
        return default


def _raw_date(raw: dict[str, Any], *paths: str, default: date) -> date:
    return _parse_date(_pick(raw, *paths), default)


def _period_start(period_ref: str) -> date:
    try:
        parsed = datetime.strptime(period_ref, "%Y-%m").date()
        return parsed.replace(day=1)
    except ValueError:
        return date.today().replace(day=1)


def _stable_id(prefix: str, raw: dict[str, Any], *preferred_parts: str) -> str:
    for part in preferred_parts:
        value = _to_str(part)
        if value:
            return f"{prefix}:{value[:80]}"

    payload = json.dumps(raw, sort_keys=True, ensure_ascii=True, default=str)
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def map_customer(raw: dict[str, Any]) -> dict[str, Any]:
    external_id = _raw_str(
        raw,
        "codigo_cliente_omie",
        "codigo_cliente_integracao",
        "id",
        "cnpj_cpf",
    )
    if not external_id:
        external_id = _stable_id(
            "omie-customer",
            raw,
            _raw_str(raw, "cnpj_cpf"),
            _raw_str(raw, "razao_social"),
            _raw_str(raw, "nome_fantasia"),
        )

    legal_name = _raw_str(raw, "razao_social", "nome_fantasia", default="Cliente Omie")
    trade_name = _raw_str(raw, "nome_fantasia", "razao_social", default=legal_name)
    is_inactive = _raw_str(raw, "inativo", default="N").upper() == "S"

    return {
        "external_id": external_id,
        "source_record_id": external_id,
        "name": legal_name,
        "legal_name": legal_name,
        "trade_name": trade_name,
        "document": _raw_str(raw, "cnpj_cpf", "cpf_cnpj", default=""),
        "status": "inactive" if is_inactive else "active",
        "email": _raw_str(raw, "email", "email1", default=""),
        "phone": _raw_str(raw, "telefone1_numero", "telefone1_ddd", "telefone", default=""),
    }


def map_product(raw: dict[str, Any]) -> dict[str, Any]:
    external_id = _raw_str(raw, "codigo_produto", "codigo_produto_integracao", "id", "codigo")
    if not external_id:
        external_id = _stable_id(
            "omie-product",
            raw,
            _raw_str(raw, "codigo"),
            _raw_str(raw, "descricao"),
        )

    status = "inactive" if _raw_str(raw, "inativo", default="N").upper() == "S" else "active"

    return {
        "external_id": external_id,
        "source_record_id": external_id,
        "sku": _raw_str(raw, "codigo", "codigo_produto", default=external_id),
        "name": _raw_str(raw, "descricao", "descricao_produto", default="Produto Omie"),
        "category": _raw_str(raw, "ncm", "departamento", "familia", default="Geral"),
        "unit": _raw_str(raw, "unidade", "un", default="UN"),
        "status": status,
        "default_cost": _raw_float(raw, "valor_custo", "custo_medio", "custo", default=0.0),
        "default_price": _raw_float(raw, "valor_unitario", "valor_venda", "preco", default=0.0),
    }


def map_sale(raw: dict[str, Any], *, period_ref: str) -> dict[str, Any]:
    default_date = _period_start(period_ref)
    source_record_id = _raw_str(raw, "codigo_pedido", "id", "numero_pedido", "cabecalho.codigo_pedido")
    if not source_record_id:
        source_record_id = _stable_id(
            "omie-sale",
            raw,
            _raw_str(raw, "numero_pedido"),
            _raw_str(raw, "id"),
        )

    gross = _raw_float(raw, "valor_total_pedido", "valor_total", "total_geral", default=0.0)
    tax = _raw_float(raw, "valor_impostos", "valor_imposto", "valor_tributos", default=0.0)
    discount = _raw_float(raw, "valor_desconto", "desconto", default=0.0)
    returned = _raw_float(raw, "valor_devolucao", "valor_estorno", default=0.0)
    net_default = gross - tax - discount - returned
    net = _raw_float(raw, "valor_liquido", "total_liquido", default=net_default)

    return {
        "source_record_id": source_record_id,
        "period_ref": period_ref,
        "transaction_date": _raw_date(
            raw,
            "data_emissao",
            "cabecalho.data_previsao",
            "data_pedido",
            default=default_date,
        ),
        "invoice_id": _raw_str(
            raw,
            "numero_pedido",
            "codigo_pedido",
            "cabecalho.numero_pedido",
            "numero_documento",
            default=source_record_id,
        ),
        "invoice_line_id": _raw_str(raw, "sequencia_item", "numero_item", "item", "n_item", default="1"),
        "product_external_id": _raw_str(raw, "codigo_produto", "item.codigo_produto", "produto_id", default="prd-omie"),
        "customer_external_id": _raw_str(
            raw,
            "codigo_cliente",
            "codigo_cliente_omie",
            "cabecalho.codigo_cliente",
            "cliente_id",
            default="cli-omie",
        ),
        "gross_revenue": gross,
        "tax_amount": tax,
        "discount_amount": discount,
        "return_amount": returned,
        "net_revenue": net,
        "quantity_sold": _raw_float(raw, "quantidade", "item.quantidade", "quantidade_total", default=1.0),
        "cogs_amount": _raw_float(raw, "custo_total", "valor_custo_total", "valor_custo", default=0.0),
    }


def map_accounts_receivable(raw: dict[str, Any], *, period_ref: str) -> dict[str, Any]:
    default_issue = _period_start(period_ref)
    source_record_id = _raw_str(raw, "codigo_lancamento", "codigo_lancamento_omie", "nCodTitulo", "id")
    if not source_record_id:
        source_record_id = _stable_id(
            "omie-ar",
            raw,
            _raw_str(raw, "numero_documento"),
            _raw_str(raw, "id"),
        )

    issue = _raw_date(raw, "data_emissao", "data_lancamento", "data", default=default_issue)
    due = _raw_date(raw, "data_vencimento", "vencimento", default=issue)

    payment_value = _pick(raw, "data_pagamento", "data_recebimento", "data_baixa")
    payment_date = _parse_date(payment_value, issue) if payment_value is not None else None

    amount = _raw_float(raw, "valor_documento", "valor_titulo", "valor", default=0.0)
    received = _raw_float(raw, "valor_recebido", "valor_pago", default=0.0)
    outstanding = _raw_float(raw, "valor_aberto", "saldo", default=max(amount - received, 0.0))

    return {
        "source_record_id": source_record_id,
        "period_ref": period_ref,
        "customer_id": _raw_str(raw, "codigo_cliente", "codigo_cliente_omie", "cliente.codigo", default="cli-omie"),
        "invoice_number": _raw_str(raw, "numero_documento", "numero_titulo", "numero", default=source_record_id),
        "issue_date": issue,
        "due_date": due,
        "payment_date": payment_date,
        "amount": amount,
        "received_amount": received,
        "outstanding_amount": outstanding,
        "status": _raw_str(raw, "status", "status_titulo", default="open"),
        "aging_days": _raw_int(raw, "dias_atraso", "atraso", default=0),
    }


def map_accounts_payable(raw: dict[str, Any], *, period_ref: str) -> dict[str, Any]:
    default_issue = _period_start(period_ref)
    source_record_id = _raw_str(raw, "codigo_lancamento", "codigo_lancamento_omie", "nCodTitulo", "id")
    if not source_record_id:
        source_record_id = _stable_id(
            "omie-ap",
            raw,
            _raw_str(raw, "numero_documento"),
            _raw_str(raw, "id"),
        )

    issue = _raw_date(raw, "data_emissao", "data_lancamento", "data", default=default_issue)
    due = _raw_date(raw, "data_vencimento", "vencimento", default=issue)

    payment_value = _pick(raw, "data_pagamento", "data_baixa")
    payment_date = _parse_date(payment_value, issue) if payment_value is not None else None

    amount = _raw_float(raw, "valor_documento", "valor_titulo", "valor", default=0.0)
    paid = _raw_float(raw, "valor_pago", "valor_recebido", default=0.0)
    outstanding = _raw_float(raw, "valor_aberto", "saldo", default=max(amount - paid, 0.0))

    return {
        "source_record_id": source_record_id,
        "period_ref": period_ref,
        "supplier_id": _raw_str(raw, "codigo_fornecedor", "codigo_cliente_fornecedor", default="for-omie"),
        "invoice_number": _raw_str(raw, "numero_documento", "numero_titulo", "numero", default=source_record_id),
        "issue_date": issue,
        "due_date": due,
        "payment_date": payment_date,
        "amount": amount,
        "paid_amount": paid,
        "outstanding_amount": outstanding,
        "status": _raw_str(raw, "status", "status_titulo", default="open"),
        "aging_days": _raw_int(raw, "dias_atraso", "atraso", default=0),
    }


def map_cashflow(raw: dict[str, Any], *, period_ref: str) -> dict[str, Any]:
    default_date = _period_start(period_ref)
    source_record_id = _raw_str(raw, "codigo_lancamento", "codigo_movimento", "id", "nCodMovimento")
    if not source_record_id:
        source_record_id = _stable_id(
            "omie-cashflow",
            raw,
            _raw_str(raw, "descricao"),
            _raw_str(raw, "id"),
        )

    in_value = _raw_float(raw, "valor_entrada", "valor_credito", "valor_recebido", default=0.0)
    out_value = _raw_float(raw, "valor_saida", "valor_debito", "valor_pago", default=0.0)

    if in_value == 0.0 and out_value == 0.0:
        total = _raw_float(raw, "valor", default=0.0)
        flow_hint = _raw_str(raw, "tipo_fluxo", "tipo", "natureza", default="").lower()
        if flow_hint in {"credit", "entrada", "receita", "recebimento"}:
            in_value = total
        elif flow_hint in {"debit", "saida", "despesa", "pagamento"}:
            out_value = total

    return {
        "source_record_id": source_record_id,
        "period_ref": period_ref,
        "transaction_date": _raw_date(raw, "data_lancamento", "data_movimento", "data", default=default_date),
        "cash_flow_type": _raw_str(raw, "tipo_fluxo", "tipo", "natureza", default="operational"),
        "account_type": _raw_str(raw, "conta", "codigo_conta", "descricao_conta", "conta_corrente", default="default"),
        "cash_in_amount": in_value,
        "cash_out_amount": out_value,
        "operating_cash_flow_amount": _raw_float(raw, "operating_cash_flow_amount", "valor_operacional", default=in_value - out_value),
        "description": _raw_str(raw, "descricao", "historico", "complemento", default="omie cashflow entry"),
    }


def map_inventory(raw: dict[str, Any], *, period_ref: str) -> dict[str, Any]:
    default_date = _period_start(period_ref)
    source_record_id = _raw_str(raw, "codigo_item", "id", "codigo_produto", "produto.codigo")
    if not source_record_id:
        source_record_id = _stable_id(
            "omie-inventory",
            raw,
            _raw_str(raw, "codigo_produto"),
            _raw_str(raw, "id"),
        )

    opening = _raw_float(raw, "estoque_inicial", "saldo_inicial", "quantidade_inicial", default=0.0)
    closing = _raw_float(raw, "estoque_final", "quantidade_estoque", "saldo_final", "quantidade", default=opening)
    if opening == 0.0 and closing != 0.0:
        opening = closing

    average_quantity = _raw_float(raw, "average_quantity", "quantidade_media", default=(opening + closing) / 2)
    average_cost = _raw_float(raw, "custo_medio", "valor_custo_medio", "custo", "valor_unitario", default=0.0)
    inventory_value = _raw_float(raw, "inventory_value", "valor_estoque", default=closing * average_cost)

    return {
        "source_record_id": source_record_id,
        "period_ref": period_ref,
        "product_id": _raw_str(raw, "codigo_produto", "id_produto", "produto.codigo", default="prd-omie"),
        "warehouse_id": _raw_str(
            raw,
            "codigo_almoxarifado",
            "codigo_deposito",
            "id_almoxarifado",
            "deposito.codigo",
            default="wh-omie",
        ),
        "snapshot_date": _raw_date(raw, "data_snapshot", "data_posicao", "data", default=default_date),
        "opening_quantity": opening,
        "closing_quantity": closing,
        "average_quantity": average_quantity,
        "average_cost": average_cost,
        "inventory_value": inventory_value,
        "stock_turnover": _raw_float(raw, "giro", "giro_estoque", default=0.0),
        "days_in_inventory": _raw_float(raw, "dias_estoque", "cobertura_dias", default=0.0),
    }


def map_hr(raw: dict[str, Any], *, period_ref: str) -> dict[str, Any]:
    source_record_id = _raw_str(raw, "codigo_lote", "codigo_folha", "id", "periodo")
    if not source_record_id:
        source_record_id = f"hr:{period_ref}"

    employee_count = _raw_int(raw, "colaboradores_total", "funcionarios_total", "qtde_colaboradores", default=0)
    active = _raw_int(raw, "colaboradores_ativos", "funcionarios_ativos", "ativos", default=employee_count)
    terminated_default = max(employee_count - active, 0)
    terminated = _raw_int(raw, "colaboradores_desligados", "funcionarios_desligados", "desligados", default=terminated_default)

    payroll = _raw_float(raw, "folha_total", "folha_pagamento", "total_folha", default=0.0)
    average_salary_default = payroll / active if active > 0 else 0.0
    average_salary = _raw_float(raw, "average_salary", "salario_medio", default=average_salary_default)

    return {
        "source_record_id": source_record_id,
        "period_ref": period_ref,
        "employee_count": employee_count,
        "active_employee_count": active,
        "terminated_employee_count": terminated,
        "payroll_amount": payroll,
        "average_salary": average_salary,
        "hours_worked": _raw_float(raw, "horas_trabalhadas", "horas_total", "total_horas", default=0.0),
    }
