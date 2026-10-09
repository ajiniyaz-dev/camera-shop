from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.columns import created_at, updated_at
from app.models.brand import LOCALE_CHECK

if TYPE_CHECKING:
    from app.models.product import Product


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint(
            "source_code IS NULL OR source_code IN ('hikvision', 'ezviz')",
            name="ck_categories_source_code",
        ),
        Index(
            "uq_categories_sibling_slug",
            text("COALESCE(parent_id, 0)"),
            "slug",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", name="fk_categories_parent_id", ondelete="RESTRICT")
    )
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    source_code: Mapped[str | None] = mapped_column(Text)
    source_worksheet: Mapped[str | None] = mapped_column(Text)
    source_heading: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    parent: Mapped[Category | None] = relationship(
        back_populates="children",
        remote_side=[id],
        foreign_keys=[parent_id],
    )
    children: Mapped[list[Category]] = relationship(
        back_populates="parent",
        foreign_keys=[parent_id],
        passive_deletes=True,
    )
    translations: Mapped[list[CategoryTranslation]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    products: Mapped[list[Product]] = relationship(
        "Product",
        back_populates="category",
        passive_deletes=True,
    )


class CategoryTranslation(Base):
    __tablename__ = "category_translations"
    __table_args__ = (CheckConstraint(LOCALE_CHECK, name="ck_category_translations_locale"),)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", name="fk_category_translations_category_id", ondelete="CASCADE"),
        primary_key=True,
    )
    locale: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    seo_title: Mapped[str | None] = mapped_column(Text)
    seo_description: Mapped[str | None] = mapped_column(Text)

    category: Mapped[Category] = relationship(back_populates="translations")
