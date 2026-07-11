from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "demo" / "nova_distribuidora"

COMPANY = {
    "company_id": "cmp_nova_distribuidora",
    "legal_name": "Nova Distribuidora Brasil Ltda.",
    "trade_name": "Nova Distribuidora Brasil",
    "segment": "Distribuidora de materiais eletricos e hidraulicos",
    "city": "Campinas",
    "state": "SP",
    "years_in_business": 12,
    "employees": 48,
    "active_customers": 620,
    "suppliers": 85,
    "products": 1350,
}


def _month_range() -> list[date]:
    today = date.today().replace(day=1)
    months: list[date] = []
    for idx in range(23, -1, -1):
        year = today.year
        month = today.month - idx
        while month <= 0:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        months.append(date(year, month, 1))
    return months


MONTHS = _month_range()


def _money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _write_csv(filename: str, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path = OUT_DIR / filename
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


@dataclass(slots=True)
class SaleHeader:
    sale_id: str
    order_id: str
    invoice_id: str
    customer_external_id: str
    order_date: date
    gross: Decimal
    tax: Decimal
    discount: Decimal
    returned: Decimal
    net: Decimal
    cogs: Decimal


def _generate_customers() -> tuple[list[dict[str, str]], list[str]]:
    sectors = [
        "Construtora",
        "Instaladora",
        "Industria",
        "Varejo",
        "Condominial",
        "Hospitalar",
        "Hotelaria",
        "Publico",
    ]
    rows: list[dict[str, str]] = []
    customer_ids: list[str] = []

    for i in range(1, 621):
        ext_id = f"CLI-{i:04d}"
        customer_ids.append(ext_id)
        status = "active" if i % 29 != 0 else "inactive"
        city_suffix = ["Campinas", "Sumare", "Valinhos", "Hortolandia", "Paulinia"][i % 5]
        rows.append(
            {
                "source_record_id": f"SRC-CUST-{i:05d}",
                "legal_name": f"Cliente {i:04d} Comercio e Servicos Ltda",
                "trade_name": f"Cliente {i:04d}",
                "document_number": f"{13000000000000 + i}",
                "status": status,
                "billing_street": f"Rua Comercial {((i - 1) % 180) + 1}",
                "billing_number": str((i % 250) + 1),
                "billing_district": "Distrito Industrial" if i % 4 == 0 else "Centro",
                "billing_city": city_suffix,
                "billing_state": "SP",
                "billing_country": "Brasil",
                "billing_postal_code": f"130{(i % 90):02d}{(i % 100):03d}",
                "contact_email": f"financeiro{i:04d}@cliente.com.br",
                "contact_phone": f"19{900000000 + i:09d}",
                "external_id": ext_id,
            }
        )

    return rows, customer_ids


def _generate_products() -> tuple[list[dict[str, str]], list[str], dict[str, str]]:
    categories = [
        "Cabos e Fios",
        "Disjuntores",
        "Tomadas e Interruptores",
        "Iluminacao LED",
        "Conexoes PVC",
        "Tubos e Eletrodutos",
        "Bombas Hidraulicas",
        "Ferramentas",
        "Fixacao",
        "Painel Eletrico",
        "Valvulas",
        "Acessorios Hidraulicos",
    ]
    units = ["UN", "CX", "MT", "RL"]

    rows: list[dict[str, str]] = []
    product_ids: list[str] = []
    category_map: dict[str, str] = {}

    for i in range(1, 1351):
        ext_id = f"PRD-{i:05d}"
        sku = f"SKU-NDB-{i:05d}"
        cat = categories[i % len(categories)]
        category_map[ext_id] = cat
        product_ids.append(ext_id)

        base_cost = Decimal("8") + Decimal(i % 120) * Decimal("0.90")
        margin_factor = Decimal("1.38") if i % 7 else Decimal("1.28")
        default_price = base_cost * margin_factor

        rows.append(
            {
                "source_record_id": f"SRC-PROD-{i:05d}",
                "sku": sku,
                "name": f"{cat} Modelo {i:04d}",
                "category": cat,
                "unit_of_measure": units[i % len(units)],
                "status": "active" if i % 41 != 0 else "inactive",
                "default_cost": _money(base_cost),
                "default_price": _money(default_price),
                "tax_profile_ref": "ICMS18",
                "external_id": ext_id,
            }
        )

    return rows, product_ids, category_map


def _season_factor(month: int) -> Decimal:
    # Sazonalidade realista para distribuição B2B: pico em nov/dez e mar/abr.
    if month in (11, 12):
        return Decimal("1.18")
    if month in (3, 4):
        return Decimal("1.08")
    if month in (1, 2, 7):
        return Decimal("0.92")
    return Decimal("1.00")


def _generate_sales_and_orders(
    customer_ids: list[str],
    product_ids: list[str],
) -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[SaleHeader],
]:
    sales_rows: list[dict[str, str]] = []
    orders_rows: list[dict[str, str]] = []
    order_items_rows: list[dict[str, str]] = []
    sales_meta: list[SaleHeader] = []

    top_customers = customer_ids[:15]

    for i in range(1, 18001):
        month_idx = (i - 1) % 24
        month_ref = MONTHS[month_idx]
        day = (i % 28) + 1
        order_date = month_ref.replace(day=day)

        if i % 100 < 35:
            customer_ext = top_customers[i % len(top_customers)]
        else:
            customer_ext = customer_ids[(i * 17) % len(customer_ids)]

        seasonal = _season_factor(order_date.month)
        # Ticket medio com tendencia de queda no ultimo ano para criar problema real.
        trend_discount = Decimal("1.00") - (Decimal(max(0, month_idx - 12)) * Decimal("0.006"))
        gross = (Decimal("2150") + Decimal((i % 70) * 35)) * seasonal * trend_discount
        gross = gross.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        tax = (gross * Decimal("0.18")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        discount = (gross * (Decimal("0.035") + Decimal((i % 5)) * Decimal("0.002"))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Devolucoes sobem no segundo ano.
        return_rate = Decimal("0.008") + Decimal(max(0, month_idx - 12)) * Decimal("0.0011")
        returned = (gross * return_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        net = gross - tax - discount - returned

        # Custo sobe ao longo do tempo, pressionando margem.
        cogs_rate = Decimal("0.60") + Decimal(month_idx) * Decimal("0.0042")
        cogs = (gross * cogs_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        sale_id = f"S-{i:06d}"
        order_id = f"O-{i:06d}"
        invoice_id = f"NF-{i:06d}"

        sales_rows.append(
            {
                "source_record_id": f"SRC-SALE-{i:06d}",
                "transaction_date": order_date.isoformat(),
                "invoice_id": invoice_id,
                "invoice_line_id": "1",
                "product_external_id": product_ids[(i * 13) % len(product_ids)],
                "customer_external_id": customer_ext,
                "gross_revenue": _money(gross),
                "tax_amount": _money(tax),
                "discount_amount": _money(discount),
                "return_amount": _money(returned),
                "net_revenue": _money(net),
                "quantity_sold": str((i % 9) + 1),
                "cogs_amount": _money(cogs),
            }
        )

        orders_rows.append(
            {
                "order_id": order_id,
                "company_id": COMPANY["company_id"],
                "customer_external_id": customer_ext,
                "order_date": order_date.isoformat(),
                "status": "faturado",
                "gross_amount": _money(gross),
                "net_amount": _money(net),
                "sales_channel": ["Balcao", "Televendas", "Representante", "E-commerce B2B"][i % 4],
            }
        )

        # 90.000 itens: 5 por pedido.
        for j in range(1, 6):
            item_idx = ((i - 1) * 5) + j
            unit_price = (gross / Decimal("5") / Decimal((j % 3) + 1)).quantize(Decimal("0.01"))
            qty = Decimal((j % 3) + 1)
            line_total = (unit_price * qty).quantize(Decimal("0.01"))
            order_items_rows.append(
                {
                    "order_item_id": f"OI-{item_idx:07d}",
                    "order_id": order_id,
                    "product_external_id": product_ids[(item_idx * 19) % len(product_ids)],
                    "quantity": str(int(qty)),
                    "unit_price": _money(unit_price),
                    "line_total": _money(line_total),
                }
            )

        sales_meta.append(
            SaleHeader(
                sale_id=sale_id,
                order_id=order_id,
                invoice_id=invoice_id,
                customer_external_id=customer_ext,
                order_date=order_date,
                gross=gross,
                tax=tax,
                discount=discount,
                returned=returned,
                net=net,
                cogs=cogs,
            )
        )

    return sales_rows, orders_rows, order_items_rows, sales_meta


def _generate_suppliers() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for i in range(1, 86):
        # Atraso recorrente em alguns fornecedores criticos.
        delay_profile = "alto" if i in (3, 7, 11, 19, 23) else ("medio" if i % 6 == 0 else "baixo")
        rows.append(
            {
                "supplier_id": f"SUP-{i:03d}",
                "company_id": COMPANY["company_id"],
                "legal_name": f"Fornecedor {i:03d} Industria e Comercio Ltda",
                "document_number": f"{22000000000000 + i}",
                "city": ["Campinas", "Jundiai", "Sao Paulo", "Sorocaba"][i % 4],
                "state": "SP",
                "lead_time_days": str(7 + (i % 18)),
                "delivery_delay_profile": delay_profile,
                "payment_term_days": str(21 + (i % 45)),
                "category_focus": ["Eletrico", "Hidraulico", "Ferramentas", "Iluminacao"][i % 4],
            }
        )
    return rows


def _generate_inventory_and_movements(product_ids: list[str], category_map: dict[str, str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    inventory_rows: list[dict[str, str]] = []
    movement_rows: list[dict[str, str]] = []

    stale_products = set(product_ids[-140:])

    for idx, product in enumerate(product_ids, start=1):
        on_hand = 35 + (idx % 180)
        reserved = idx % 11
        available = on_hand - reserved

        if product in stale_products:
            on_hand += 140
            available += 140
            days_wo = 180 + (idx % 90)
            last_move = (date.today() - timedelta(days=days_wo)).isoformat()
        else:
            days_wo = 3 + (idx % 35)
            last_move = (date.today() - timedelta(days=days_wo)).isoformat()

        inventory_value = Decimal(on_hand) * (Decimal("9") + Decimal(idx % 70) * Decimal("0.85"))

        if idx <= 250:
            abc = "A"
        elif idx <= 700:
            abc = "B"
        else:
            abc = "C"

        inventory_rows.append(
            {
                "product_external_id": product,
                "category": category_map[product],
                "on_hand_qty": str(on_hand),
                "reserved_qty": str(reserved),
                "available_qty": str(available),
                "inventory_value": _money(inventory_value),
                "days_without_movement": str(days_wo),
                "abc_class": abc,
                "last_movement_date": last_move,
            }
        )

    # 60.000 movimentacoes (exceto itens parados).
    active_products = [p for p in product_ids if p not in stale_products]
    for i in range(1, 60001):
        month_idx = (i - 1) % 24
        ref = MONTHS[month_idx]
        move_date = ref.replace(day=(i % 28) + 1)
        product = active_products[(i * 7) % len(active_products)]
        move_type = ["entrada_compra", "saida_venda", "ajuste"][i % 3]
        qty = (i % 30) + 1
        movement_rows.append(
            {
                "movement_id": f"MOV-{i:07d}",
                "product_external_id": product,
                "movement_date": move_date.isoformat(),
                "movement_type": move_type,
                "quantity": str(qty),
                "unit_cost": _money(Decimal("8") + Decimal(i % 80) * Decimal("0.65")),
                "warehouse": ["CD-Campinas", "CD-Interior"][i % 2],
                "document_ref": f"DOC-{i:07d}",
            }
        )

    return inventory_rows, movement_rows


def _generate_receivables(sales_meta: list[SaleHeader]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    receivable_rows: list[dict[str, str]] = []
    receipts_rows: list[dict[str, str]] = []

    installments_total = 0
    for idx, sale in enumerate(sales_meta, start=1):
        plan = 1
        if idx % 4 == 0:
            plan += 1
        if idx % 12 == 0:
            plan += 1
        if idx % 20 == 0:
            plan += 1
        if idx <= 100:
            plan += 1

        base_amount = (sale.net / Decimal(plan)).quantize(Decimal("0.01"))
        for inst in range(1, plan + 1):
            installments_total += 1
            if installments_total > 25000:
                break

            due_days = 28 + (inst * 15)
            due_date = sale.order_date + timedelta(days=due_days)

            # Inadimplencia e aumento do prazo medio de recebimento no periodo recente.
            recent_penalty = 12 if sale.order_date >= MONTHS[-8] else 0
            client_risk = 18 if int(sale.customer_external_id.split("-")[1]) % 13 == 0 else 0
            delay_days = (idx % 9) + recent_penalty + client_risk

            status = "recebido"
            received_date = due_date + timedelta(days=max(0, delay_days - 6))
            if delay_days > 22:
                status = "vencido"
                received_date = None

            receivable_id = f"AR-{installments_total:07d}"
            receivable_rows.append(
                {
                    "receivable_id": receivable_id,
                    "sale_id": sale.sale_id,
                    "customer_external_id": sale.customer_external_id,
                    "issue_date": sale.order_date.isoformat(),
                    "due_date": due_date.isoformat(),
                    "amount": _money(base_amount),
                    "status": status,
                    "days_overdue": str(max(0, delay_days) if status == "vencido" else 0),
                }
            )

            if received_date is not None:
                receipts_rows.append(
                    {
                        "receipt_id": f"RC-{len(receipts_rows) + 1:07d}",
                        "receivable_id": receivable_id,
                        "customer_external_id": sale.customer_external_id,
                        "received_date": received_date.isoformat(),
                        "amount_received": _money(base_amount),
                        "payment_method": ["Boleto", "PIX", "Transferencia"][idx % 3],
                    }
                )

        if installments_total >= 25000:
            break

    # Completa recebimentos ate 25.000 com liquidacoes parciais de titulos pagos.
    paid_receivables = [r for r in receivable_rows if r["status"] == "recebido"]
    cursor = 0
    while len(receipts_rows) < 25000 and paid_receivables:
        rec = paid_receivables[cursor % len(paid_receivables)]
        due = date.fromisoformat(rec["due_date"])
        receipts_rows.append(
            {
                "receipt_id": f"RC-{len(receipts_rows) + 1:07d}",
                "receivable_id": rec["receivable_id"],
                "customer_external_id": rec["customer_external_id"],
                "received_date": (due + timedelta(days=2 + (cursor % 6))).isoformat(),
                "amount_received": _money(Decimal(rec["amount"]) * Decimal("0.15")),
                "payment_method": ["Boleto", "PIX", "Transferencia"][cursor % 3],
            }
        )
        cursor += 1

    return receivable_rows, receipts_rows


def _generate_purchases_and_payables(suppliers: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    purchase_rows: list[dict[str, str]] = []
    payable_rows: list[dict[str, str]] = []
    payment_rows: list[dict[str, str]] = []

    supplier_ids = [s["supplier_id"] for s in suppliers]

    payables_count = 0
    for i in range(1, 11001):
        month_idx = (i - 1) % 24
        ref = MONTHS[month_idx]
        purchase_date = ref.replace(day=(i % 28) + 1)
        supplier = supplier_ids[(i * 5) % len(supplier_ids)]

        gross = Decimal("1800") + Decimal(i % 90) * Decimal("42")
        # Custo de compra cresce ao longo do periodo.
        gross *= Decimal("1.00") + Decimal(month_idx) * Decimal("0.008")
        gross = gross.quantize(Decimal("0.01"))

        promised_days = 10 + (i % 18)
        delayed = supplier in {"SUP-003", "SUP-007", "SUP-011", "SUP-019", "SUP-023"}
        extra_delay = 8 + (i % 7) if delayed else (i % 3)
        delivery_date = purchase_date + timedelta(days=promised_days + extra_delay)

        purchase_id = f"PO-{i:06d}"
        purchase_rows.append(
            {
                "purchase_id": purchase_id,
                "supplier_id": supplier,
                "purchase_date": purchase_date.isoformat(),
                "expected_delivery_date": (purchase_date + timedelta(days=promised_days)).isoformat(),
                "actual_delivery_date": delivery_date.isoformat(),
                "status": "entregue" if delivery_date <= date.today() else "aberto",
                "gross_amount": _money(gross),
                "delay_days": str(max(0, (delivery_date - (purchase_date + timedelta(days=promised_days))).days)),
            }
        )

        inst = 1 if i % 4 else 2
        amount_per = (gross / Decimal(inst)).quantize(Decimal("0.01"))
        for part in range(1, inst + 1):
            payables_count += 1
            if payables_count > 14000:
                break

            due_date = purchase_date + timedelta(days=25 + (part * 18))
            status = "pago"
            pay_date = due_date + timedelta(days=(i % 5) - 2)

            payable_id = f"AP-{payables_count:07d}"
            payable_rows.append(
                {
                    "payable_id": payable_id,
                    "purchase_id": purchase_id,
                    "supplier_id": supplier,
                    "issue_date": purchase_date.isoformat(),
                    "due_date": due_date.isoformat(),
                    "amount": _money(amount_per),
                    "status": status,
                    "days_overdue": str(max(0, (date.today() - due_date).days) if status == "vencido" else 0),
                }
            )

            payment_rows.append(
                {
                    "payment_id": f"PM-{len(payment_rows) + 1:07d}",
                    "payable_id": payable_id,
                    "supplier_id": supplier,
                    "payment_date": pay_date.isoformat(),
                    "amount_paid": _money(amount_per),
                    "payment_method": ["Boleto", "TED", "PIX"][i % 3],
                }
            )

        if payables_count >= 14000 and len(payment_rows) >= 14000:
            break

    # Garante volume exato solicitado para contas a pagar e pagamentos.
    while payables_count < 14000:
        payables_count += 1
        supplier = supplier_ids[payables_count % len(supplier_ids)]
        issue_date = MONTHS[payables_count % 24].replace(day=(payables_count % 28) + 1)
        due_date = issue_date + timedelta(days=30)
        amount = Decimal("1200") + Decimal(payables_count % 50) * Decimal("19")
        payable_id = f"AP-{payables_count:07d}"
        payable_rows.append(
            {
                "payable_id": payable_id,
                "purchase_id": f"PO-EX-{payables_count:06d}",
                "supplier_id": supplier,
                "issue_date": issue_date.isoformat(),
                "due_date": due_date.isoformat(),
                "amount": _money(amount),
                "status": "pago",
                "days_overdue": "0",
            }
        )
        payment_rows.append(
            {
                "payment_id": f"PM-{len(payment_rows) + 1:07d}",
                "payable_id": payable_id,
                "supplier_id": supplier,
                "payment_date": (due_date + timedelta(days=2)).isoformat(),
                "amount_paid": _money(amount),
                "payment_method": "PIX",
            }
        )

    if len(payment_rows) > 14000:
        payment_rows[:] = payment_rows[:14000]

    return purchase_rows, payable_rows, payment_rows


def _generate_financial_template(receipts: list[dict[str, str]], payments: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    # Entradas de recebimentos
    for i, receipt in enumerate(receipts[:14000], start=1):
        amount = Decimal(receipt["amount_received"])
        out = Decimal("0.00")
        rows.append(
            {
                "source_record_id": f"SRC-FIN-IN-{i:07d}",
                "transaction_date": receipt["received_date"],
                "cash_flow_type": "operating",
                "account_type": "accounts_receivable",
                "cash_in_amount": _money(amount),
                "cash_out_amount": _money(out),
                "operating_cash_flow_amount": _money(amount - out),
                "description": f"Recebimento titulo {receipt['receivable_id']}",
            }
        )

    # Saidas de pagamentos
    for i, payment in enumerate(payments[:11000], start=1):
        amount = Decimal(payment["amount_paid"])
        rows.append(
            {
                "source_record_id": f"SRC-FIN-OUT-{i:07d}",
                "transaction_date": payment["payment_date"],
                "cash_flow_type": "operating",
                "account_type": "accounts_payable",
                "cash_in_amount": _money(Decimal("0.00")),
                "cash_out_amount": _money(amount),
                "operating_cash_flow_amount": _money(Decimal("0.00") - amount),
                "description": f"Pagamento titulo {payment['payable_id']}",
            }
        )

    # Ajustes administrativos (crescimento de despesas)
    for i in range(1, 1201):
        ref = MONTHS[(i - 1) % 24]
        trans_date = ref.replace(day=((i * 3) % 28) + 1)
        expense = Decimal("350") + Decimal(i % 40) * Decimal("11") + Decimal((i - 1) // 50) * Decimal("25")
        rows.append(
            {
                "source_record_id": f"SRC-FIN-ADM-{i:07d}",
                "transaction_date": trans_date.isoformat(),
                "cash_flow_type": "operating",
                "account_type": "administrative_expense",
                "cash_in_amount": "0.00",
                "cash_out_amount": _money(expense),
                "operating_cash_flow_amount": _money(Decimal("0.00") - expense),
                "description": "Despesa administrativa recorrente",
            }
        )

    return rows


def _generate_cash_flow(financial_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    running = Decimal("950000.00")

    for idx, row in enumerate(sorted(financial_rows, key=lambda x: x["transaction_date"]), start=1):
        cash_in = Decimal(row["cash_in_amount"])
        cash_out = Decimal(row["cash_out_amount"])
        running += cash_in - cash_out
        rows.append(
            {
                "entry_id": f"CF-{idx:07d}",
                "transaction_date": row["transaction_date"],
                "origin": row["account_type"],
                "cash_in": _money(cash_in),
                "cash_out": _money(cash_out),
                "balance_after": _money(running),
                "description": row["description"],
            }
        )

    return rows


def _generate_expenses_and_dre(
    sales_meta: list[SaleHeader],
    receipts: list[dict[str, str]],
    payments: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    # Estruturas de controle.
    cost_centers = [
        {"cost_center_id": "CC-ADM", "name": "Administrativo", "type": "despesa"},
        {"cost_center_id": "CC-COM", "name": "Comercial", "type": "despesa"},
        {"cost_center_id": "CC-LOG", "name": "Logistica", "type": "custo"},
        {"cost_center_id": "CC-EST", "name": "Estoque", "type": "custo"},
        {"cost_center_id": "CC-FIN", "name": "Financeiro", "type": "despesa"},
    ]

    chart = [
        {"account_code": "3.1.1", "account_name": "Receita Bruta", "nature": "revenue"},
        {"account_code": "3.1.2", "account_name": "Impostos sobre Vendas", "nature": "deduction"},
        {"account_code": "3.1.3", "account_name": "Descontos", "nature": "deduction"},
        {"account_code": "3.1.4", "account_name": "Devolucoes", "nature": "deduction"},
        {"account_code": "4.1.1", "account_name": "CMV", "nature": "cost"},
        {"account_code": "5.1.1", "account_name": "Despesas Comerciais", "nature": "expense"},
        {"account_code": "5.1.2", "account_name": "Despesas Administrativas", "nature": "expense"},
        {"account_code": "5.1.3", "account_name": "Despesas Financeiras", "nature": "expense"},
        {"account_code": "9.9.9", "account_name": "Resultado Liquido", "nature": "result"},
    ]

    # Agregacoes mensais.
    monthly = {
        m.strftime("%Y-%m"): {
            "gross": Decimal("0"),
            "tax": Decimal("0"),
            "discount": Decimal("0"),
            "returned": Decimal("0"),
            "net": Decimal("0"),
            "cogs": Decimal("0"),
        }
        for m in MONTHS
    }

    for sale in sales_meta:
        key = sale.order_date.strftime("%Y-%m")
        monthly[key]["gross"] += sale.gross
        monthly[key]["tax"] += sale.tax
        monthly[key]["discount"] += sale.discount
        monthly[key]["returned"] += sale.returned
        monthly[key]["net"] += sale.net
        monthly[key]["cogs"] += sale.cogs

    expenses_rows: list[dict[str, str]] = []
    dre_rows: list[dict[str, str]] = []
    costs_rows: list[dict[str, str]] = []

    for idx, m in enumerate(MONTHS, start=1):
        key = m.strftime("%Y-%m")
        data = monthly[key]

        # Despesas administrativas em crescimento (problema real).
        admin_exp = data["gross"] * (Decimal("0.07") + Decimal(idx) * Decimal("0.0011"))
        comm_exp = data["gross"] * (Decimal("0.045") + Decimal((idx % 6)) * Decimal("0.0008"))
        fin_exp = data["gross"] * (Decimal("0.012") + Decimal(max(0, idx - 16)) * Decimal("0.0006"))

        expenses_rows.extend(
            [
                {
                    "expense_id": f"EXP-ADM-{idx:03d}",
                    "period": key,
                    "cost_center_id": "CC-ADM",
                    "account_code": "5.1.2",
                    "amount": _money(admin_exp),
                    "description": "Folha administrativa, TI, servicos e estrutura",
                },
                {
                    "expense_id": f"EXP-COM-{idx:03d}",
                    "period": key,
                    "cost_center_id": "CC-COM",
                    "account_code": "5.1.1",
                    "amount": _money(comm_exp),
                    "description": "Comissoes, campanhas e incentivos comerciais",
                },
                {
                    "expense_id": f"EXP-FIN-{idx:03d}",
                    "period": key,
                    "cost_center_id": "CC-FIN",
                    "account_code": "5.1.3",
                    "amount": _money(fin_exp),
                    "description": "Juros, tarifas bancarias e custo de capital de giro",
                },
            ]
        )

        costs_rows.extend(
            [
                {
                    "cost_id": f"COST-LOG-{idx:03d}",
                    "period": key,
                    "cost_center_id": "CC-LOG",
                    "amount": _money(data["cogs"] * Decimal("0.11")),
                    "description": "Fretes e operacao logistica",
                },
                {
                    "cost_id": f"COST-EST-{idx:03d}",
                    "period": key,
                    "cost_center_id": "CC-EST",
                    "amount": _money(data["cogs"] * Decimal("0.06")),
                    "description": "Custos de armazenagem e perdas de estoque",
                },
            ]
        )

        ebitda = data["net"] - data["cogs"] - admin_exp - comm_exp
        net_profit = ebitda - fin_exp
        net_margin = (net_profit / data["gross"] * Decimal("100")) if data["gross"] else Decimal("0")

        dre_rows.append(
            {
                "period": key,
                "gross_revenue": _money(data["gross"]),
                "taxes": _money(data["tax"]),
                "discounts": _money(data["discount"]),
                "returns": _money(data["returned"]),
                "net_revenue": _money(data["net"]),
                "cogs": _money(data["cogs"]),
                "gross_profit": _money(data["net"] - data["cogs"]),
                "commercial_expenses": _money(comm_exp),
                "administrative_expenses": _money(admin_exp),
                "ebitda": _money(ebitda),
                "financial_expenses": _money(fin_exp),
                "net_profit": _money(net_profit),
                "net_margin_pct": _money(net_margin),
            }
        )

    return expenses_rows, dre_rows, costs_rows, chart, cost_centers


def _generate_categories(category_map: dict[str, str]) -> list[dict[str, str]]:
    seen = sorted(set(category_map.values()))
    return [
        {
            "category_id": f"CAT-{idx:03d}",
            "name": name,
            "segment": "Eletrico/Hidraulico",
        }
        for idx, name in enumerate(seen, start=1)
    ]


def _generate_users() -> list[dict[str, str]]:
    roles = [
        "ceo",
        "cfo",
        "controller",
        "sales_director",
        "operations_manager",
        "buyer",
        "analyst",
    ]
    rows: list[dict[str, str]] = []
    for i in range(1, 49):
        role = roles[i % len(roles)]
        rows.append(
            {
                "user_id": f"USR-{i:03d}",
                "company_id": COMPANY["company_id"],
                "name": f"Usuario {i:03d}",
                "email": f"usuario{i:03d}@novadistribuidora.com.br",
                "role": role,
                "is_active": "true" if i % 17 != 0 else "false",
            }
        )
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    customers_rows, customer_ids = _generate_customers()
    products_rows, product_ids, category_map = _generate_products()
    sales_rows, orders_rows, order_items_rows, sales_meta = _generate_sales_and_orders(customer_ids, product_ids)
    suppliers_rows = _generate_suppliers()
    inventory_rows, movement_rows = _generate_inventory_and_movements(product_ids, category_map)
    receivable_rows, receipts_rows = _generate_receivables(sales_meta)
    purchases_rows, payable_rows, payment_rows = _generate_purchases_and_payables(suppliers_rows)
    financial_rows = _generate_financial_template(receipts_rows, payment_rows)
    cash_flow_rows = _generate_cash_flow(financial_rows)
    expenses_rows, dre_rows, costs_rows, chart_rows, cost_centers_rows = _generate_expenses_and_dre(
        sales_meta, receipts_rows, payment_rows
    )

    company_row = [
        {
            "company_id": COMPANY["company_id"],
            "legal_name": COMPANY["legal_name"],
            "trade_name": COMPANY["trade_name"],
            "segment": COMPANY["segment"],
            "city": COMPANY["city"],
            "state": COMPANY["state"],
            "years_in_business": str(COMPANY["years_in_business"]),
            "employees": str(COMPANY["employees"]),
            "active_customers": str(COMPANY["active_customers"]),
            "suppliers": str(COMPANY["suppliers"]),
            "products": str(COMPANY["products"]),
            "annual_revenue_target": "18000000.00",
            "avg_net_margin_target_pct": "11.00",
        }
    ]

    categories_rows = _generate_categories(category_map)
    users_rows = _generate_users()

    # Mandatory files requested by user.
    _write_csv(
        "customers.csv",
        [
            "source_record_id",
            "legal_name",
            "trade_name",
            "document_number",
            "status",
            "billing_street",
            "billing_number",
            "billing_district",
            "billing_city",
            "billing_state",
            "billing_country",
            "billing_postal_code",
            "contact_email",
            "contact_phone",
            "external_id",
        ],
        customers_rows,
    )
    _write_csv(
        "products.csv",
        [
            "source_record_id",
            "sku",
            "name",
            "category",
            "unit_of_measure",
            "status",
            "default_cost",
            "default_price",
            "tax_profile_ref",
            "external_id",
        ],
        products_rows,
    )
    _write_csv(
        "sales.csv",
        [
            "source_record_id",
            "transaction_date",
            "invoice_id",
            "invoice_line_id",
            "product_external_id",
            "customer_external_id",
            "gross_revenue",
            "tax_amount",
            "discount_amount",
            "return_amount",
            "net_revenue",
            "quantity_sold",
            "cogs_amount",
        ],
        sales_rows,
    )
    _write_csv(
        "financial.csv",
        [
            "source_record_id",
            "transaction_date",
            "cash_flow_type",
            "account_type",
            "cash_in_amount",
            "cash_out_amount",
            "operating_cash_flow_amount",
            "description",
        ],
        financial_rows,
    )

    _write_csv(
        "suppliers.csv",
        [
            "supplier_id",
            "company_id",
            "legal_name",
            "document_number",
            "city",
            "state",
            "lead_time_days",
            "delivery_delay_profile",
            "payment_term_days",
            "category_focus",
        ],
        suppliers_rows,
    )
    _write_csv(
        "inventory.csv",
        [
            "product_external_id",
            "category",
            "on_hand_qty",
            "reserved_qty",
            "available_qty",
            "inventory_value",
            "days_without_movement",
            "abc_class",
            "last_movement_date",
        ],
        inventory_rows,
    )
    _write_csv(
        "accounts_payable.csv",
        [
            "payable_id",
            "purchase_id",
            "supplier_id",
            "issue_date",
            "due_date",
            "amount",
            "status",
            "days_overdue",
        ],
        payable_rows,
    )
    _write_csv(
        "accounts_receivable.csv",
        [
            "receivable_id",
            "sale_id",
            "customer_external_id",
            "issue_date",
            "due_date",
            "amount",
            "status",
            "days_overdue",
        ],
        receivable_rows,
    )
    _write_csv(
        "cash_flow.csv",
        [
            "entry_id",
            "transaction_date",
            "origin",
            "cash_in",
            "cash_out",
            "balance_after",
            "description",
        ],
        cash_flow_rows,
    )
    _write_csv(
        "purchases.csv",
        [
            "purchase_id",
            "supplier_id",
            "purchase_date",
            "expected_delivery_date",
            "actual_delivery_date",
            "status",
            "gross_amount",
            "delay_days",
        ],
        purchases_rows,
    )
    _write_csv(
        "expenses.csv",
        [
            "expense_id",
            "period",
            "cost_center_id",
            "account_code",
            "amount",
            "description",
        ],
        expenses_rows,
    )
    _write_csv(
        "dre.csv",
        [
            "period",
            "gross_revenue",
            "taxes",
            "discounts",
            "returns",
            "net_revenue",
            "cogs",
            "gross_profit",
            "commercial_expenses",
            "administrative_expenses",
            "ebitda",
            "financial_expenses",
            "net_profit",
            "net_margin_pct",
        ],
        dre_rows,
    )

    # Additional datasets to cover complete operating model.
    _write_csv("company.csv", list(company_row[0].keys()), company_row)
    _write_csv("users.csv", list(users_rows[0].keys()), users_rows)
    _write_csv("categories.csv", list(categories_rows[0].keys()), categories_rows)
    _write_csv("orders.csv", list(orders_rows[0].keys()), orders_rows)
    _write_csv("order_items.csv", list(order_items_rows[0].keys()), order_items_rows)
    _write_csv("stock_movements.csv", list(movement_rows[0].keys()), movement_rows)
    _write_csv("receipts.csv", list(receipts_rows[0].keys()), receipts_rows)
    _write_csv("payments.csv", list(payment_rows[0].keys()), payment_rows)
    _write_csv("chart_of_accounts.csv", list(chart_rows[0].keys()), chart_rows)
    _write_csv("cost_centers.csv", list(cost_centers_rows[0].keys()), cost_centers_rows)
    _write_csv("costs.csv", list(costs_rows[0].keys()), costs_rows)

    summary = {
        "customers": len(customers_rows),
        "products": len(products_rows),
        "sales": len(sales_rows),
        "orders": len(orders_rows),
        "order_items": len(order_items_rows),
        "accounts_receivable": len(receivable_rows),
        "accounts_payable": len(payable_rows),
        "stock_movements": len(movement_rows),
        "receipts": len(receipts_rows),
        "payments": len(payment_rows),
    }
    print("Generated dataset in:", OUT_DIR)
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
