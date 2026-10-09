from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, Identity, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.columns import created_at, updated_at

if TYPE_CHECKING:
    from app.models.product import Product

LOCALE_CHECK = "locale IN ('ru', 'uz', 'en')"


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    translations: Mapped[list[BrandTranslation]] = relationship(
        back_populates="brand",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    products: Mapped[list[Product]] = relationship(
        "Product",
        back_populates="brand",
        passive_deletes=True,
    )


class BrandTranslation(Base):
    __tablename__ = "brand_translations"
    __table_args__ = (CheckConstraint(LOCALE_CHECK, name="ck_brand_translations_locale"),)

    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id", name="fk_brand_translations_brand_id", ondelete="CASCADE"),
        primary_key=True,
    )
    locale: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    seo_title: Mapped[str | None] = mapped_column(Text)
    seo_description: Mapped[str | None] = mapped_column(Text)

    brand: Mapped[Brand] = relationship(back_populates="translations")
