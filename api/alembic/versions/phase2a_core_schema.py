"""Core catalog schema.

Revision ID: phase2a_core
Revises:
Create Date: 2026-10-09

Import jobs, admin sessions, the audit log, and slug redirects are Phase 2B.
``product_source_records.first_job_id`` and ``last_job_id`` are stored here
without a foreign key until ``import_jobs`` exists.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "phase2a_core"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LOCALE_CHECK = "locale IN ('ru', 'uz', 'en')"
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
SOURCE_PRICE_CHECK = """
(
  (source_price_kind = 'numeric'
    AND source_price_amount IS NOT NULL
    AND source_price_amount >= 0)
  OR (source_price_kind = 'explicit_on_request' AND source_price_amount IS NULL)
  OR (source_price_kind = 'blank' AND source_price_amount IS NULL)
)
"""


def upgrade() -> None:
    op.create_table(
        "brands",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_brands_slug"),
    )
    op.create_table(
        "brand_translations",
        sa.Column("brand_id", sa.BigInteger(), nullable=False),
        sa.Column("locale", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("seo_title", sa.Text(), nullable=True),
        sa.Column("seo_description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["brand_id"], ["brands.id"], name="fk_brand_translations_brand_id", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("brand_id", "locale", name="pk_brand_translations"),
        sa.CheckConstraint(LOCALE_CHECK, name="ck_brand_translations_locale"),
    )
    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=True),
        sa.Column("source_worksheet", sa.Text(), nullable=True),
        sa.Column("source_heading", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["categories.id"], name="fk_categories_parent_id", ondelete="RESTRICT"
        ),
        sa.CheckConstraint(
            "source_code IS NULL OR source_code IN ('hikvision', 'ezviz')",
            name="ck_categories_source_code",
        ),
    )
    op.create_index(
        "uq_categories_sibling_slug",
        "categories",
        [sa.text("COALESCE(parent_id, 0)"), "slug"],
        unique=True,
    )
    op.create_table(
        "category_translations",
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.Column("locale", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("seo_title", sa.Text(), nullable=True),
        sa.Column("seo_description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_category_translations_category_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("category_id", "locale", name="pk_category_translations"),
        sa.CheckConstraint(LOCALE_CHECK, name="ck_category_translations_locale"),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("brand_id", sa.BigInteger(), nullable=True),
        sa.Column("category_id", sa.BigInteger(), nullable=True),
        sa.Column("product_kind", sa.Text(), nullable=False),
        sa.Column("model_raw", sa.Text(), nullable=False),
        sa.Column("model_display", sa.Text(), nullable=False),
        sa.Column("model_normalized", sa.Text(), nullable=False),
        sa.Column("option_label", sa.Text(), nullable=True),
        sa.Column("public_price_status", sa.Text(), nullable=False),
        sa.Column("public_price_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("public_currency", sa.CHAR(3), nullable=True),
        sa.Column("price_locked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("option_locked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("brand_locked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("category_locked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("model_locked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("stock_status", sa.Text(), server_default=sa.text("'in_stock'"), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("catalog_status", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("price_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["brand_id"], ["brands.id"], name="fk_products_brand_id", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], name="fk_products_category_id", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("slug", name="uq_products_slug"),
        sa.CheckConstraint(PUBLIC_PRICE_CHECK, name="ck_products_public_price"),
        sa.CheckConstraint(
            "stock_status IN ('in_stock', 'out_of_stock')",
            name="ck_products_stock_status",
        ),
        sa.CheckConstraint(
            "catalog_status IN ('draft', 'published', 'archived')",
            name="ck_products_catalog_status",
        ),
        sa.CheckConstraint(
            "product_kind IN ('product', 'service')",
            name="ck_products_product_kind",
        ),
    )
    op.create_index("ix_products_brand_id", "products", ["brand_id"])
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index(
        "ix_products_catalog_status_deleted_at",
        "products",
        ["catalog_status", "deleted_at"],
    )
    op.create_index("ix_products_model_normalized", "products", ["model_normalized"])
    op.create_table(
        "product_translations",
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("locale", sa.Text(), nullable=False),
        sa.Column("localized_name", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("seo_title", sa.Text(), nullable=True),
        sa.Column("seo_description", sa.Text(), nullable=True),
        sa.Column(
            "description_locked", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("origin", sa.Text(), nullable=False),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_translations_product_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("product_id", "locale", name="pk_product_translations"),
        sa.CheckConstraint(LOCALE_CHECK, name="ck_product_translations_locale"),
        sa.CheckConstraint(
            "origin IN ('source', 'manual', 'empty')",
            name="ck_product_translations_origin",
        ),
    )
    op.create_table(
        "product_specifications",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_specifications_product_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_product_specifications_product_id",
        "product_specifications",
        ["product_id"],
    )
    op.create_table(
        "product_specification_translations",
        sa.Column("specification_id", sa.BigInteger(), nullable=False),
        sa.Column("locale", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["specification_id"],
            ["product_specifications.id"],
            name="fk_product_specification_translations_specification_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "specification_id",
            "locale",
            name="pk_product_specification_translations",
        ),
        sa.CheckConstraint(LOCALE_CHECK, name="ck_product_specification_translations_locale"),
    )
    op.create_table(
        "product_source_records",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("source_workbook", sa.Text(), nullable=False),
        sa.Column("source_worksheet", sa.Text(), nullable=False),
        sa.Column("source_row", sa.Integer(), nullable=False),
        sa.Column("source_line_number", sa.Text(), nullable=True),
        sa.Column("source_model_raw", sa.Text(), nullable=False),
        sa.Column("source_option_raw", sa.Text(), nullable=True),
        sa.Column("source_description_raw", sa.Text(), nullable=True),
        sa.Column("source_description_sha256", sa.CHAR(64), nullable=True),
        sa.Column("source_price_header", sa.Text(), nullable=True),
        sa.Column("source_price_raw", sa.Text(), nullable=True),
        sa.Column("source_price_kind", sa.Text(), nullable=False),
        sa.Column("source_price_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("section_label", sa.Text(), nullable=True),
        sa.Column("parent_section_label", sa.Text(), nullable=True),
        sa.Column("internal_note", sa.Text(), nullable=True),
        sa.Column("match_key", sa.Text(), nullable=False),
        sa.Column("first_job_id", sa.BigInteger(), nullable=False),
        sa.Column("last_job_id", sa.BigInteger(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "absent_from_latest", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_source_records_product_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("product_id", name="uq_product_source_records_product_id"),
        sa.UniqueConstraint("match_key", name="uq_product_source_records_match_key"),
        sa.CheckConstraint(
            "source_code IN ('hikvision', 'ezviz')",
            name="ck_product_source_records_source_code",
        ),
        sa.CheckConstraint(SOURCE_PRICE_CHECK, name="ck_product_source_records_price"),
    )
    op.create_index(
        "ix_product_source_records_source",
        "product_source_records",
        ["source_code", "source_worksheet"],
    )
    op.create_index(
        "ix_product_source_records_absent",
        "product_source_records",
        ["absent_from_latest"],
    )
    op.create_table(
        "product_images",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("storage_backend", sa.Text(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.CHAR(64), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("alt_text", sa.Text(), nullable=True),
        sa.Column("association_status", sa.Text(), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=True),
        sa.Column("source_worksheet", sa.Text(), nullable=True),
        sa.Column("anchor_row", sa.Integer(), nullable=True),
        sa.Column("anchor_col", sa.Integer(), nullable=True),
        sa.Column("anchor_to_row", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_images_product_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "storage_backend IN ('local', 's3')",
            name="ck_product_images_storage_backend",
        ),
        sa.CheckConstraint(
            "mime_type IN ('image/png', 'image/jpeg', 'image/webp')",
            name="ck_product_images_mime_type",
        ),
        sa.CheckConstraint(
            "association_status IN ('high', 'needs_review', 'confirmed', 'rejected')",
            name="ck_product_images_association_status",
        ),
        sa.CheckConstraint(
            "source_code IS NULL OR source_code IN ('hikvision', 'ezviz')",
            name="ck_product_images_source_code",
        ),
    )
    op.create_index("ix_product_images_product_id", "product_images", ["product_id"])
    op.create_index(
        "uq_product_images_one_primary",
        "product_images",
        ["product_id"],
        unique=True,
        postgresql_where=sa.text("is_primary AND association_status <> 'rejected'"),
    )
    op.create_table(
        "business_profile",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("public_name", sa.Text(), server_default=sa.text("'HikVision'"), nullable=False),
        sa.Column("legal_name", sa.Text(), nullable=True),
        sa.Column("domain", sa.Text(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("opening_hours", sa.Text(), nullable=True),
        sa.Column("social_links", postgresql.JSONB(), nullable=True),
        sa.Column("logo_object_key", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_business_profile_singleton"),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO business_profile (id, public_name)
            VALUES (1, 'HikVision')
            """
        )
    )
    op.create_table(
        "admin_users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_admin_users_email"),
        sa.CheckConstraint("role = 'admin'", name="ck_admin_users_role"),
    )


def downgrade() -> None:
    op.drop_table("admin_users")
    op.drop_table("business_profile")
    op.drop_index("uq_product_images_one_primary", table_name="product_images")
    op.drop_index("ix_product_images_product_id", table_name="product_images")
    op.drop_table("product_images")
    op.drop_index("ix_product_source_records_absent", table_name="product_source_records")
    op.drop_index("ix_product_source_records_source", table_name="product_source_records")
    op.drop_table("product_source_records")
    op.drop_table("product_specification_translations")
    op.drop_index("ix_product_specifications_product_id", table_name="product_specifications")
    op.drop_table("product_specifications")
    op.drop_table("product_translations")
    op.drop_index("ix_products_model_normalized", table_name="products")
    op.drop_index("ix_products_catalog_status_deleted_at", table_name="products")
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_index("ix_products_brand_id", table_name="products")
    op.drop_table("products")
    op.drop_table("category_translations")
    op.drop_index("uq_categories_sibling_slug", table_name="categories")
    op.drop_table("categories")
    op.drop_table("brand_translations")
    op.drop_table("brands")
