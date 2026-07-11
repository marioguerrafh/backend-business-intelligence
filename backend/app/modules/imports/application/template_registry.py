from __future__ import annotations

from dataclasses import dataclass

from app.modules.imports.application.contracts import ImportTemplate


@dataclass(slots=True, frozen=True)
class TemplateDefinition:
    template: ImportTemplate
    required_headers: tuple[str, ...]


TEMPLATES: dict[ImportTemplate, TemplateDefinition] = {
    "customers": TemplateDefinition(
        template="customers",
        required_headers=(
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
        ),
    ),
    "products": TemplateDefinition(
        template="products",
        required_headers=(
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
        ),
    ),
    "sales": TemplateDefinition(
        template="sales",
        required_headers=(
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
        ),
    ),
    "financial": TemplateDefinition(
        template="financial",
        required_headers=(
            "source_record_id",
            "transaction_date",
            "cash_flow_type",
            "account_type",
            "cash_in_amount",
            "cash_out_amount",
            "operating_cash_flow_amount",
            "description",
        ),
    ),
}


def get_template(template: ImportTemplate) -> TemplateDefinition:
    return TEMPLATES[template]
