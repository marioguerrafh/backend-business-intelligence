"""initial schema

Revision ID: 20260710_0001
Revises:
Create Date: 2026-07-10 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260710_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_refresh_sessions",
        sa.Column("token_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_token_id", sa.String(length=64), nullable=True),
        sa.PrimaryKeyConstraint("token_id"),
    )
    op.create_index("ix_auth_refresh_sessions_company_id", "auth_refresh_sessions", ["company_id"])
    op.create_index("ix_auth_refresh_sessions_user_id", "auth_refresh_sessions", ["user_id"])

    op.create_table(
        "auth_users",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_auth_users_email", "auth_users", ["email"])

    op.create_table(
        "business_customer_ingestion_records",
        sa.Column("ingestion_record_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("ingestion_record_id"),
        sa.UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_business_customer_ingestion_record",
        ),
    )
    op.create_index(
        "ix_business_customer_ingestion_records_company_id",
        "business_customer_ingestion_records",
        ["company_id"],
    )
    op.create_index(
        "ix_business_customer_ingestion_records_customer_id",
        "business_customer_ingestion_records",
        ["customer_id"],
    )

    op.create_table(
        "business_customers",
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("trade_name", sa.String(length=255), nullable=True),
        sa.Column("document_number", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("billing_street", sa.String(length=255), nullable=True),
        sa.Column("billing_number", sa.String(length=32), nullable=True),
        sa.Column("billing_district", sa.String(length=120), nullable=True),
        sa.Column("billing_city", sa.String(length=120), nullable=True),
        sa.Column("billing_state", sa.String(length=64), nullable=True),
        sa.Column("billing_country", sa.String(length=64), nullable=True),
        sa.Column("billing_postal_code", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("customer_id"),
        sa.UniqueConstraint("company_id", "document_number", name="uq_business_customer_document"),
    )
    op.create_index("ix_business_customers_company_id", "business_customers", ["company_id"])

    op.create_table(
        "business_products",
        sa.Column("product_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("unit_of_measure", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("default_cost", sa.String(length=64), nullable=False),
        sa.Column("default_price", sa.String(length=64), nullable=False),
        sa.Column("tax_profile_ref", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("product_id"),
        sa.UniqueConstraint("company_id", "sku", name="uq_business_product_sku"),
    )
    op.create_index("ix_business_products_company_id", "business_products", ["company_id"])

    op.create_table(
        "business_product_ingestion_records",
        sa.Column("ingestion_record_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("product_id", sa.String(length=64), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("ingestion_record_id"),
        sa.UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_business_product_ingestion_record",
        ),
    )
    op.create_index(
        "ix_business_product_ingestion_records_company_id",
        "business_product_ingestion_records",
        ["company_id"],
    )
    op.create_index(
        "ix_business_product_ingestion_records_product_id",
        "business_product_ingestion_records",
        ["product_id"],
    )

    op.create_table(
        "auth_user_memberships",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "company_id", "role", name="uq_auth_membership_role"),
    )
    op.create_index("ix_auth_user_memberships_company_id", "auth_user_memberships", ["company_id"])
    op.create_index("ix_auth_user_memberships_user_id", "auth_user_memberships", ["user_id"])

    op.create_table(
        "business_customer_contacts",
        sa.Column("contact_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("channel_type", sa.String(length=32), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["business_customers.customer_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("contact_id"),
        sa.UniqueConstraint("customer_id", "channel_type", "value", name="uq_business_customer_contact"),
    )
    op.create_index("ix_business_customer_contacts_customer_id", "business_customer_contacts", ["customer_id"])

    op.create_table(
        "business_customer_external_refs",
        sa.Column("external_ref_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["business_customers.customer_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("external_ref_id"),
        sa.UniqueConstraint(
            "company_id",
            "source_system",
            "external_id",
            name="uq_business_customer_external_ref",
        ),
    )
    op.create_index(
        "ix_business_customer_external_refs_company_id",
        "business_customer_external_refs",
        ["company_id"],
    )
    op.create_index(
        "ix_business_customer_external_refs_customer_id",
        "business_customer_external_refs",
        ["customer_id"],
    )

    op.create_table(
        "business_product_external_refs",
        sa.Column("external_ref_id", sa.String(length=64), nullable=False),
        sa.Column("product_id", sa.String(length=64), nullable=False),
        sa.Column("company_id", sa.String(length=64), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["business_products.product_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("external_ref_id"),
        sa.UniqueConstraint(
            "company_id",
            "source_system",
            "external_id",
            name="uq_business_product_external_ref",
        ),
    )
    op.create_index(
        "ix_business_product_external_refs_company_id",
        "business_product_external_refs",
        ["company_id"],
    )
    op.create_index("ix_business_product_external_refs_product_id", "business_product_external_refs", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_business_product_external_refs_product_id", table_name="business_product_external_refs")
    op.drop_index("ix_business_product_external_refs_company_id", table_name="business_product_external_refs")
    op.drop_table("business_product_external_refs")

    op.drop_index("ix_business_customer_external_refs_customer_id", table_name="business_customer_external_refs")
    op.drop_index("ix_business_customer_external_refs_company_id", table_name="business_customer_external_refs")
    op.drop_table("business_customer_external_refs")

    op.drop_index("ix_business_customer_contacts_customer_id", table_name="business_customer_contacts")
    op.drop_table("business_customer_contacts")

    op.drop_index("ix_auth_user_memberships_user_id", table_name="auth_user_memberships")
    op.drop_index("ix_auth_user_memberships_company_id", table_name="auth_user_memberships")
    op.drop_table("auth_user_memberships")

    op.drop_index("ix_business_product_ingestion_records_product_id", table_name="business_product_ingestion_records")
    op.drop_index("ix_business_product_ingestion_records_company_id", table_name="business_product_ingestion_records")
    op.drop_table("business_product_ingestion_records")

    op.drop_index("ix_business_products_company_id", table_name="business_products")
    op.drop_table("business_products")

    op.drop_index("ix_business_customers_company_id", table_name="business_customers")
    op.drop_table("business_customers")

    op.drop_index("ix_business_customer_ingestion_records_customer_id", table_name="business_customer_ingestion_records")
    op.drop_index("ix_business_customer_ingestion_records_company_id", table_name="business_customer_ingestion_records")
    op.drop_table("business_customer_ingestion_records")

    op.drop_index("ix_auth_users_email", table_name="auth_users")
    op.drop_table("auth_users")

    op.drop_index("ix_auth_refresh_sessions_user_id", table_name="auth_refresh_sessions")
    op.drop_index("ix_auth_refresh_sessions_company_id", table_name="auth_refresh_sessions")
    op.drop_table("auth_refresh_sessions")
