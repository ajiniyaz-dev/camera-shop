"""Staged import jobs. Parsing writes these tables; applying a job is later work.

Job status uses the documented values. They cover the requested lifecycle:

- upload: the job and its ``import_files`` rows exist
- validation: ``import_files.validation_status`` and ``validation_errors``
- review: ``import_jobs.status = preview``, plus each row's ``resolution``
- applying: ``applying``
- completed: ``applied``
- failed: ``failed``

``rejected`` is the documented state for a review the administrator discards.
A missing workbook is the absence of that source's ``import_files`` row. It is
not a delete. ``publish_new_products`` is the job's publish choice for new
rows and defaults to true. ``replace_prices`` stays false until an
administrator explicitly chooses to overwrite manual prices.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

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
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.columns import created_at

if TYPE_CHECKING:
    from app.models.admin_user import AdminUser
    from app.models.product import Product

JOB_STATUS_CHECK = "status IN ('preview', 'rejected', 'applying', 'applied', 'failed')"
SOURCE_CODE_CHECK = "source_code IN ('hikvision', 'ezviz')"
FILE_VALIDATION_CHECK = """
(
  jsonb_typeof(validation_errors) = 'array'
  AND (
    validation_status = 'valid'
    OR (
      validation_status = 'invalid'
      AND included_in_apply = false
      AND jsonb_array_length(validation_errors) > 0
    )
  )
)
"""
ROW_APPLY_CHECK = """
NOT (
  applied
  AND (
    action IN ('exclude', 'skip')
    OR classification = 'invalid'
    OR (action IN ('possible_match', 'conflict') AND resolution = 'pending')
  )
)
"""
APPLIED_TIMESTAMP_CHECK = """
(
  (status = 'applied' AND applied_at IS NOT NULL)
  OR (status <> 'applied' AND applied_at IS NULL)
)
"""
APPROVAL_CHECK = """
(
  (status IN ('preview', 'rejected') AND approved_by IS NULL)
  OR status IN ('applying', 'applied', 'failed')
)
"""


class ImportJob(Base):
    """One review and one apply action, containing one or both workbooks."""

    __tablename__ = "import_jobs"
    __table_args__ = (
        CheckConstraint(JOB_STATUS_CHECK, name="ck_import_jobs_status"),
        CheckConstraint(APPLIED_TIMESTAMP_CHECK, name="ck_import_jobs_applied_at"),
        CheckConstraint(APPROVAL_CHECK, name="ck_import_jobs_approved_by"),
        CheckConstraint(
            "summary IS NULL OR jsonb_typeof(summary) = 'object'",
            name="ck_import_jobs_summary",
        ),
        Index("ix_import_jobs_status", "status"),
        Index("ix_import_jobs_created_by", "created_by"),
        Index("ix_import_jobs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'preview'")
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("admin_users.id", name="fk_import_jobs_created_by", ondelete="RESTRICT"),
        nullable=False,
    )
    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", name="fk_import_jobs_approved_by", ondelete="RESTRICT")
    )
    replace_prices: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    publish_new_products: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        comment="When true, new products from this job start published.",
    )
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at()
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    creator: Mapped[AdminUser] = relationship(
        "AdminUser",
        foreign_keys=[created_by],
        back_populates="created_jobs",
    )
    approver: Mapped[AdminUser | None] = relationship(
        "AdminUser",
        foreign_keys=[approved_by],
        back_populates="approved_jobs",
    )
    files: Mapped[list[ImportFile]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ImportFile(Base):
    """One uploaded workbook. A job has at most one file for each source."""

    __tablename__ = "import_files"
    __table_args__ = (
        CheckConstraint(SOURCE_CODE_CHECK, name="ck_import_files_source_code"),
        CheckConstraint(
            "identification IN ('auto', 'admin_confirmed')",
            name="ck_import_files_identification",
        ),
        CheckConstraint(
            "validation_status IN ('valid', 'invalid')",
            name="ck_import_files_validation_status",
        ),
        CheckConstraint(FILE_VALIDATION_CHECK, name="ck_import_files_validation"),
        CheckConstraint("sha256 ~ '^[0-9a-fA-F]{64}$'", name="ck_import_files_sha256"),
        UniqueConstraint("job_id", "source_code", name="uq_import_files_job_source"),
        Index("ix_import_files_sha256", "sha256"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("import_jobs.id", name="fk_import_files_job_id", ondelete="CASCADE"),
        nullable=False,
    )
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    identification: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'auto'")
    )
    validation_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'valid'")
    )
    validation_errors: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    stored_object_key: Mapped[str] = mapped_column(Text, nullable=False)
    included_in_apply: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    job: Mapped[ImportJob] = relationship(back_populates="files")
    rows: Mapped[list[ImportRow]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    assets: Mapped[list[ImportAsset]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ImportRow(Base):
    """One staged worksheet row. Live catalog rows are not written from here."""

    __tablename__ = "import_rows"
    __table_args__ = (
        CheckConstraint(
            "classification IN ('product', 'service', 'heading', 'blank', 'stray', 'invalid')",
            name="ck_import_rows_classification",
        ),
        CheckConstraint(
            "action IN ('insert', 'update', 'unchanged', 'possible_match', 'conflict', 'exclude', 'skip')",
            name="ck_import_rows_action",
        ),
        CheckConstraint(
            "resolution IN ('pending', 'keep_current', 'accept_excel', 'accept_new')",
            name="ck_import_rows_resolution",
        ),
        CheckConstraint("source_row >= 1", name="ck_import_rows_source_row"),
        CheckConstraint("length(btrim(worksheet_name)) > 0", name="ck_import_rows_worksheet"),
        CheckConstraint("jsonb_typeof(raw_cells) = 'object'", name="ck_import_rows_raw_cells"),
        CheckConstraint("jsonb_typeof(proposal) = 'object'", name="ck_import_rows_proposal"),
        CheckConstraint("jsonb_typeof(messages) = 'array'", name="ck_import_rows_messages"),
        CheckConstraint(ROW_APPLY_CHECK, name="ck_import_rows_apply"),
        UniqueConstraint(
            "import_file_id",
            "worksheet_name",
            "source_row",
            name="uq_import_rows_file_sheet_row",
        ),
        Index("ix_import_rows_import_file_id", "import_file_id"),
        Index("ix_import_rows_matched_product_id", "matched_product_id"),
        Index("ix_import_rows_action", "action"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    import_file_id: Mapped[int] = mapped_column(
        ForeignKey("import_files.id", name="fk_import_rows_import_file_id", ondelete="CASCADE"),
        nullable=False,
    )
    worksheet_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_row: Mapped[int] = mapped_column(Integer, nullable=False)
    classification: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    resolution: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'pending'")
    )
    raw_cells: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    proposal: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    matched_product_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "products.id",
            name="fk_import_rows_matched_product_id",
            ondelete="SET NULL",
        )
    )
    messages: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    applied: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    file: Mapped[ImportFile] = relationship(back_populates="rows")
    matched_product: Mapped[Product | None] = relationship(
        "Product",
        foreign_keys=[matched_product_id],
    )


class ImportAsset(Base):
    """An extracted image, including images that are not linked to a product."""

    __tablename__ = "import_assets"
    __table_args__ = (
        CheckConstraint(
            "mime_type IN ('image/png', 'image/jpeg', 'image/webp')",
            name="ck_import_assets_mime_type",
        ),
        CheckConstraint(
            "link_status IN ('linked_high', 'linked_review', 'unassigned', 'shared_candidate')",
            name="ck_import_assets_link_status",
        ),
        CheckConstraint("sha256 ~ '^[0-9a-fA-F]{64}$'", name="ck_import_assets_sha256"),
        CheckConstraint("length(btrim(worksheet)) > 0", name="ck_import_assets_worksheet"),
        Index("ix_import_assets_import_file_id", "import_file_id"),
        Index("ix_import_assets_sha256", "sha256"),
        Index("ix_import_assets_proposed_product_id", "proposed_product_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    import_file_id: Mapped[int] = mapped_column(
        ForeignKey(
            "import_files.id",
            name="fk_import_assets_import_file_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    worksheet: Mapped[str] = mapped_column(Text, nullable=False)
    anchor_row: Mapped[int | None] = mapped_column(Integer)
    anchor_col: Mapped[int | None] = mapped_column(Integer)
    anchor_to_row: Mapped[int | None] = mapped_column(Integer)
    proposed_product_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "products.id",
            name="fk_import_assets_proposed_product_id",
            ondelete="SET NULL",
        )
    )
    link_status: Mapped[str] = mapped_column(Text, nullable=False)

    file: Mapped[ImportFile] = relationship(back_populates="assets")
    proposed_product: Mapped[Product | None] = relationship(
        "Product",
        foreign_keys=[proposed_product_id],
    )
