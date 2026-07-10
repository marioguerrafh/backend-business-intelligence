from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.infrastructure.db.base import Base


class CustomerModel(Base):
    __tablename__ = "business_customers"
    __table_args__ = (
        UniqueConstraint("company_id", "document_number", name="uq_business_customer_document"),
    )

    customer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    billing_street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billing_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    billing_district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    billing_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    billing_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    billing_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    billing_postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    contacts: Mapped[list["CustomerContactModel"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    external_refs: Mapped[list["CustomerExternalRefModel"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )


class CustomerContactModel(Base):
    __tablename__ = "business_customer_contacts"
    __table_args__ = (
        UniqueConstraint("customer_id", "channel_type", "value", name="uq_business_customer_contact"),
    )

    contact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("business_customers.customer_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)

    customer: Mapped[CustomerModel] = relationship(back_populates="contacts")


class CustomerExternalRefModel(Base):
    __tablename__ = "business_customer_external_refs"
    __table_args__ = (
        UniqueConstraint("company_id", "source_system", "external_id", name="uq_business_customer_external_ref"),
    )

    external_ref_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("business_customers.customer_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    customer: Mapped[CustomerModel] = relationship(back_populates="external_refs")


class CustomerIngestionRecordModel(Base):
    __tablename__ = "business_customer_ingestion_records"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_business_customer_ingestion_record",
        ),
    )

    ingestion_record_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class ProductModel(Base):
    __tablename__ = "business_products"
    __table_args__ = (
        UniqueConstraint("company_id", "sku", name="uq_business_product_sku"),
    )

    product_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unit_of_measure: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    default_cost: Mapped[str] = mapped_column(String(64), nullable=False)
    default_price: Mapped[str] = mapped_column(String(64), nullable=False)
    tax_profile_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    external_refs: Mapped[list["ProductExternalRefModel"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class ProductExternalRefModel(Base):
    __tablename__ = "business_product_external_refs"
    __table_args__ = (
        UniqueConstraint("company_id", "source_system", "external_id", name="uq_business_product_external_ref"),
    )

    external_ref_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("business_products.product_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    product: Mapped[ProductModel] = relationship(back_populates="external_refs")


class ProductIngestionRecordModel(Base):
    __tablename__ = "business_product_ingestion_records"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "source_system",
            "source_record_id",
            name="uq_business_product_ingestion_record",
        ),
    )

    ingestion_record_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    product_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
