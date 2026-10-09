from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.brand import LOCALE_CHECK
from app.models.columns import created_at, updated_at

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.category import Category
    from app.models.image import ProductImage
    from app.models.source import ProductSourceRecord

PUBLIC_PRICE_CHECK = """
(
  (public_price_status = 'numeric'
    AND public_price_amount IS NOT NULL
    AND public_price_amount >= 0
    AND public_currency = 'USD')
  OR (public_price_status = 'on_request'
    AND public_price_amount IS NULL
    AND public_currency IS NULL)
  OR (public_price_status = 'hidden'
    AND public_currency IS NULL
    AND (public_price_amount IS NULL OR public_price_amount >= 0))
)
"""


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(PUBLIC_PRICE_CHECK, name="ck_products_public_price"),
        CheckConstraint(
            "stock_status IN ('in_stock', 'out_of_stock')",
            name="ck_products_stock_status",
        ),
        CheckConstraint(
            "catalog_status IN ('draft', 'published', 'archived')",
            name="ck_products_catalog_status",
        ),
        CheckConstraint(
            "product_kind IN ('product', 'service')",
            name="ck_products_product_kind",
        ),
        Index("ix_products_catalog_status_deleted_at", "catalog_status", "deleted_at"),
        Index("ix_products_model_normalized", "model_normalized"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    brand_id: Mapped[int | None] = mapped_column(
        ForeignKey("brands.id", name="fk_products_brand_id", ondelete="RESTRICT"),
        index=True,
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", name="fk_products_category_id", ondelete="RESTRICT"),
        index=True,
    )
    product_kind: Mapped[str] = mapped_column(Text, nullable=False)
    model_raw: Mapped[str] = mapped_column(Text, nullable=False)
    model_display: Mapped[str] = mapped_column(Text, nullable=False)
    model_normalized: Mapped[str] = mapped_column(Text, nullable=False)
    option_label: Mapped[str | None] = mapped_column(Text)
    public_price_status: Mapped[str] = mapped_column(Text, nullable=False)
    public_price_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    public_currency: Mapped[str | None] = mapped_column(CHAR(3))
    price_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    option_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    brand_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    category_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    model_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    stock_status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'in_stock'"))
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    catalog_status: Mapped[str] = mapped_column(Text, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()
    price_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    brand: Mapped[Brand | None] = relationship(back_populates="products")
    category: Mapped[Category | None] = relationship(back_populates="products")
    translations: Mapped[list[ProductTranslation]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    specifications: Mapped[list[ProductSpecification]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    source_record: Mapped[ProductSourceRecord | None] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    images: Mapped[list[ProductImage]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ProductTranslation(Base):
    __tablename__ = "product_translations"
    __table_args__ = (
        CheckConstraint(LOCALE_CHECK, name="ck_product_translations_locale"),
        CheckConstraint(
            "origin IN ('source', 'manual', 'empty')",
            name="ck_product_translations_origin",
        ),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", name="fk_product_translations_product_id", ondelete="CASCADE"),
        primary_key=True,
    )
    locale: Mapped[str] = mapped_column(Text, primary_key=True)
    localized_name: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    seo_title: Mapped[str | None] = mapped_column(Text)
    seo_description: Mapped[str | None] = mapped_column(Text)
    description_locked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    origin: Mapped[str] = mapped_column(Text, nullable=False)
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR)

    product: Mapped[Product] = relationship(back_populates="translations")


class ProductSpecification(Base):
    __tablename__ = "product_specifications"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", name="fk_product_specifications_product_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(nullable=False)

    product: Mapped[Product] = relationship(back_populates="specifications")
    translations: Mapped[list[ProductSpecificationTranslation]] = relationship(
        back_populates="specification",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ProductSpecificationTranslation(Base):
    __tablename__ = "product_specification_translations"
    __table_args__ = (
        CheckConstraint(LOCALE_CHECK, name="ck_product_specification_translations_locale"),
    )

    specification_id: Mapped[int] = mapped_column(
        ForeignKey(
            "product_specifications.id",
            name="fk_product_specification_translations_specification_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    locale: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    specification: Mapped[ProductSpecification] = relationship(back_populates="translations")
