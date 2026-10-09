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
    Integer,
    Numeric,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.imports import ImportJob
    from app.models.product import Product

SOURCE_PRICE_CHECK = """
(
  (source_price_kind = 'numeric'
    AND source_price_amount IS NOT NULL
    AND source_price_amount >= 0)
  OR (source_price_kind = 'explicit_on_request' AND source_price_amount IS NULL)
  OR (source_price_kind = 'blank' AND source_price_amount IS NULL)
)
"""


class ProductSourceRecord(Base):
    """One current workbook mapping for an imported product."""

    __tablename__ = "product_source_records"
    __table_args__ = (
        CheckConstraint(
            "source_code IN ('hikvision', 'ezviz')",
            name="ck_product_source_records_source_code",
        ),
        CheckConstraint(SOURCE_PRICE_CHECK, name="ck_product_source_records_price"),
        Index("ix_product_source_records_source", "source_code", "source_worksheet"),
        Index("ix_product_source_records_absent", "absent_from_latest"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", name="fk_product_source_records_product_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    source_workbook: Mapped[str] = mapped_column(Text, nullable=False)
    source_worksheet: Mapped[str] = mapped_column(Text, nullable=False)
    source_row: Mapped[int] = mapped_column(Integer, nullable=False)
    source_line_number: Mapped[str | None] = mapped_column(Text)
    source_model_raw: Mapped[str] = mapped_column(Text, nullable=False)
    source_option_raw: Mapped[str | None] = mapped_column(Text)
    source_description_raw: Mapped[str | None] = mapped_column(Text)
    source_description_sha256: Mapped[str | None] = mapped_column(CHAR(64))
    source_price_header: Mapped[str | None] = mapped_column(Text)
    source_price_raw: Mapped[str | None] = mapped_column(Text)
    source_price_kind: Mapped[str] = mapped_column(Text, nullable=False)
    source_price_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    section_label: Mapped[str | None] = mapped_column(Text)
    parent_section_label: Mapped[str | None] = mapped_column(Text)
    internal_note: Mapped[str | None] = mapped_column(Text)
    match_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    first_job_id: Mapped[int] = mapped_column(
        ForeignKey(
            "import_jobs.id",
            name="fk_product_source_records_first_job_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    last_job_id: Mapped[int] = mapped_column(
        ForeignKey(
            "import_jobs.id",
            name="fk_product_source_records_last_job_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    absent_from_latest: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    product: Mapped[Product] = relationship(back_populates="source_record")
    first_job: Mapped[ImportJob] = relationship(
        "ImportJob",
        foreign_keys=[first_job_id],
        passive_deletes=True,
    )
    last_job: Mapped[ImportJob] = relationship(
        "ImportJob",
        foreign_keys=[last_job_id],
        passive_deletes=True,
    )
