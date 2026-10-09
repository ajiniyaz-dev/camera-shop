from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    CHAR,
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

if TYPE_CHECKING:
    from app.models.product import Product


class ProductImage(Base):
    __tablename__ = "product_images"
    __table_args__ = (
        CheckConstraint(
            "storage_backend IN ('local', 's3')",
            name="ck_product_images_storage_backend",
        ),
        CheckConstraint(
            "mime_type IN ('image/png', 'image/jpeg', 'image/webp')",
            name="ck_product_images_mime_type",
        ),
        CheckConstraint(
            "association_status IN ('high', 'needs_review', 'confirmed', 'rejected')",
            name="ck_product_images_association_status",
        ),
        CheckConstraint(
            "source_code IS NULL OR source_code IN ('hikvision', 'ezviz')",
            name="ck_product_images_source_code",
        ),
        Index(
            "uq_product_images_one_primary",
            "product_id",
            unique=True,
            postgresql_where=text("is_primary AND association_status <> 'rejected'"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", name="fk_product_images_product_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    storage_backend: Mapped[str] = mapped_column(Text, nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    alt_text: Mapped[str | None] = mapped_column(Text)
    association_status: Mapped[str] = mapped_column(Text, nullable=False)
    source_code: Mapped[str | None] = mapped_column(Text)
    source_worksheet: Mapped[str | None] = mapped_column(Text)
    anchor_row: Mapped[int | None] = mapped_column(Integer)
    anchor_col: Mapped[int | None] = mapped_column(Integer)
    anchor_to_row: Mapped[int | None] = mapped_column(Integer)

    product: Mapped[Product] = relationship(back_populates="images")
