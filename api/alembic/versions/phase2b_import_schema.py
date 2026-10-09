"""Import jobs, staged rows, assets, and the admin audit log.

Revision ID: phase2b_import
Revises: phase2a_core
Create Date: 2026-10-10

The Phase 2A migration is unchanged. This revision adds the import tables and
foreign keys from ``product_source_records`` to ``import_jobs``. Existing
catalog rows are kept. If a source row already points at a job id, and an
administrator exists, that id is recorded as an applied backfill job so the
foreign key can be validated. If no administrator exists, the foreign keys are
added NOT VALID and the source rows stay in place.

``admin_sessions`` and ``slug_redirects`` are not created.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "phase2b_import"
down_revision: Union[str, Sequence[str], None] = "phase2a_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JOB_STATUS_CHECK = "status IN ('preview', 'rejected', 'applying', 'applied', 'failed')"
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
DETAIL_SECRET_CHECK = """
(
  detail IS NULL
  OR (
    jsonb_typeof(detail) = 'object'
    AND detail::text !~* '"(password(_hash)?|secret|session_token|token)"[[:space:]]*:'
  )
)
"""


def upgrade() -> None:
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("status", sa.Text(), server_default=sa.text("'preview'"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("approved_by", sa.BigInteger(), nullable=True),
        sa.Column(
            "replace_prices", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "publish_new_products",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
            comment="When true, new products from this job start published.",
        ),
        sa.Column("summary", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["admin_users.id"],
            name="fk_import_jobs_created_by",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["approved_by"],
            ["admin_users.id"],
            name="fk_import_jobs_approved_by",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(JOB_STATUS_CHECK, name="ck_import_jobs_status"),
        sa.CheckConstraint(
            "(status = 'applied' AND applied_at IS NOT NULL) OR (status <> 'applied' AND applied_at IS NULL)",
            name="ck_import_jobs_applied_at",
        ),
        sa.CheckConstraint(
            "(status IN ('preview', 'rejected') AND approved_by IS NULL) OR status IN ('applying', 'applied', 'failed')",
            name="ck_import_jobs_approved_by",
        ),
        sa.CheckConstraint(
            "summary IS NULL OR jsonb_typeof(summary) = 'object'",
            name="ck_import_jobs_summary",
        ),
    )
    op.create_index("ix_import_jobs_status", "import_jobs", ["status"])
    op.create_index("ix_import_jobs_created_by", "import_jobs", ["created_by"])
    op.create_index("ix_import_jobs_created_at", "import_jobs", ["created_at"])
    op.create_table(
        "import_files",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("sha256", sa.CHAR(64), nullable=False),
        sa.Column(
            "identification", sa.Text(), server_default=sa.text("'auto'"), nullable=False
        ),
        sa.Column(
            "validation_status", sa.Text(), server_default=sa.text("'valid'"), nullable=False
        ),
        sa.Column(
            "validation_errors",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("stored_object_key", sa.Text(), nullable=False),
        sa.Column(
            "included_in_apply", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["import_jobs.id"], name="fk_import_files_job_id", ondelete="CASCADE"
        ),
        sa.UniqueConstraint("job_id", "source_code", name="uq_import_files_job_source"),
        sa.CheckConstraint(
            "source_code IN ('hikvision', 'ezviz')",
            name="ck_import_files_source_code",
        ),
        sa.CheckConstraint(
            "identification IN ('auto', 'admin_confirmed')",
            name="ck_import_files_identification",
        ),
        sa.CheckConstraint(
            "validation_status IN ('valid', 'invalid')",
            name="ck_import_files_validation_status",
        ),
        sa.CheckConstraint(FILE_VALIDATION_CHECK, name="ck_import_files_validation"),
        sa.CheckConstraint("sha256 ~ '^[0-9a-fA-F]{64}$'", name="ck_import_files_sha256"),
    )
    op.create_index("ix_import_files_sha256", "import_files", ["sha256"])
    op.create_table(
        "import_rows",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("import_file_id", sa.BigInteger(), nullable=False),
        sa.Column("worksheet_name", sa.Text(), nullable=False),
        sa.Column("source_row", sa.Integer(), nullable=False),
        sa.Column("classification", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("resolution", sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column(
            "raw_cells",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "proposal",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("matched_product_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "messages",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("applied", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(
            ["import_file_id"],
            ["import_files.id"],
            name="fk_import_rows_import_file_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["matched_product_id"],
            ["products.id"],
            name="fk_import_rows_matched_product_id",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "import_file_id",
            "worksheet_name",
            "source_row",
            name="uq_import_rows_file_sheet_row",
        ),
        sa.CheckConstraint(
            "classification IN ('product', 'service', 'heading', 'blank', 'stray', 'invalid')",
            name="ck_import_rows_classification",
        ),
        sa.CheckConstraint(
            "action IN ('insert', 'update', 'unchanged', 'possible_match', 'conflict', 'exclude', 'skip')",
            name="ck_import_rows_action",
        ),
        sa.CheckConstraint(
            "resolution IN ('pending', 'keep_current', 'accept_excel', 'accept_new')",
            name="ck_import_rows_resolution",
        ),
        sa.CheckConstraint("source_row >= 1", name="ck_import_rows_source_row"),
        sa.CheckConstraint(
            "length(btrim(worksheet_name)) > 0", name="ck_import_rows_worksheet"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(raw_cells) = 'object'", name="ck_import_rows_raw_cells"
        ),
        sa.CheckConstraint("jsonb_typeof(proposal) = 'object'", name="ck_import_rows_proposal"),
        sa.CheckConstraint("jsonb_typeof(messages) = 'array'", name="ck_import_rows_messages"),
        sa.CheckConstraint(ROW_APPLY_CHECK, name="ck_import_rows_apply"),
    )
    op.create_index("ix_import_rows_import_file_id", "import_rows", ["import_file_id"])
    op.create_index("ix_import_rows_matched_product_id", "import_rows", ["matched_product_id"])
    op.create_index("ix_import_rows_action", "import_rows", ["action"])
    op.create_table(
        "import_assets",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("import_file_id", sa.BigInteger(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("sha256", sa.CHAR(64), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("worksheet", sa.Text(), nullable=False),
        sa.Column("anchor_row", sa.Integer(), nullable=True),
        sa.Column("anchor_col", sa.Integer(), nullable=True),
        sa.Column("anchor_to_row", sa.Integer(), nullable=True),
        sa.Column("proposed_product_id", sa.BigInteger(), nullable=True),
        sa.Column("link_status", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["import_file_id"],
            ["import_files.id"],
            name="fk_import_assets_import_file_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["proposed_product_id"],
            ["products.id"],
            name="fk_import_assets_proposed_product_id",
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "mime_type IN ('image/png', 'image/jpeg', 'image/webp')",
            name="ck_import_assets_mime_type",
        ),
        sa.CheckConstraint(
            "link_status IN ('linked_high', 'linked_review', 'unassigned', 'shared_candidate')",
            name="ck_import_assets_link_status",
        ),
        sa.CheckConstraint("sha256 ~ '^[0-9a-fA-F]{64}$'", name="ck_import_assets_sha256"),
        sa.CheckConstraint("length(btrim(worksheet)) > 0", name="ck_import_assets_worksheet"),
    )
    op.create_index("ix_import_assets_import_file_id", "import_assets", ["import_file_id"])
    op.create_index("ix_import_assets_sha256", "import_assets", ["sha256"])
    op.create_index(
        "ix_import_assets_proposed_product_id", "import_assets", ["proposed_product_id"]
    )
    op.create_table(
        "admin_audit_log",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=True),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("detail", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["admin_users.id"],
            name="fk_admin_audit_log_actor_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("length(btrim(action)) > 0", name="ck_admin_audit_log_action"),
        sa.CheckConstraint(
            "entity_id IS NULL OR entity_type IS NOT NULL",
            name="ck_admin_audit_log_entity",
        ),
        sa.CheckConstraint(DETAIL_SECRET_CHECK, name="ck_admin_audit_log_detail"),
    )
    op.create_index("ix_admin_audit_log_actor_id", "admin_audit_log", ["actor_id"])
    op.create_index("ix_admin_audit_log_created_at", "admin_audit_log", ["created_at"])
    op.create_index(
        "ix_admin_audit_log_entity", "admin_audit_log", ["entity_type", "entity_id"]
    )
    validated = _backfill_referenced_jobs()
    _add_source_job_foreign_keys(validated)
    op.create_index(
        "ix_product_source_records_first_job_id",
        "product_source_records",
        ["first_job_id"],
    )
    op.create_index(
        "ix_product_source_records_last_job_id",
        "product_source_records",
        ["last_job_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_product_source_records_last_job_id", table_name="product_source_records")
    op.drop_index("ix_product_source_records_first_job_id", table_name="product_source_records")
    op.drop_constraint(
        "fk_product_source_records_last_job_id",
        "product_source_records",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_product_source_records_first_job_id",
        "product_source_records",
        type_="foreignkey",
    )
    op.drop_index("ix_admin_audit_log_entity", table_name="admin_audit_log")
    op.drop_index("ix_admin_audit_log_created_at", table_name="admin_audit_log")
    op.drop_index("ix_admin_audit_log_actor_id", table_name="admin_audit_log")
    op.drop_table("admin_audit_log")
    op.drop_index("ix_import_assets_proposed_product_id", table_name="import_assets")
    op.drop_index("ix_import_assets_sha256", table_name="import_assets")
    op.drop_index("ix_import_assets_import_file_id", table_name="import_assets")
    op.drop_table("import_assets")
    op.drop_index("ix_import_rows_action", table_name="import_rows")
    op.drop_index("ix_import_rows_matched_product_id", table_name="import_rows")
    op.drop_index("ix_import_rows_import_file_id", table_name="import_rows")
    op.drop_table("import_rows")
    op.drop_index("ix_import_files_sha256", table_name="import_files")
    op.drop_table("import_files")
    op.drop_index("ix_import_jobs_created_at", table_name="import_jobs")
    op.drop_index("ix_import_jobs_created_by", table_name="import_jobs")
    op.drop_index("ix_import_jobs_status", table_name="import_jobs")
    op.drop_table("import_jobs")


def _backfill_referenced_jobs() -> bool:
    """Insert applied placeholder jobs for ids already stored by Phase 2A.

    Returns true when every referenced id exists and the new foreign keys can
    be validated. Existing source rows are never deleted.
    """

    bind = op.get_bind()
    orphan_count = bind.execute(
        sa.text(
            """
            SELECT count(*)
            FROM (
                SELECT first_job_id AS job_id FROM product_source_records
                UNION
                SELECT last_job_id FROM product_source_records
            ) refs
            WHERE NOT EXISTS (
                SELECT 1 FROM import_jobs AS jobs WHERE jobs.id = refs.job_id
            )
            """
        )
    ).scalar_one()
    if orphan_count == 0:
        return True
    admin_id = bind.execute(
        sa.text("SELECT id FROM admin_users ORDER BY id LIMIT 1")
    ).scalar_one_or_none()
    if admin_id is None:
        return False
    bind.execute(
        sa.text(
            """
            INSERT INTO import_jobs (
                id, status, created_by, replace_prices, publish_new_products,
                summary, applied_at
            )
            OVERRIDING SYSTEM VALUE
            SELECT
                refs.job_id,
                'applied',
                :admin_id,
                false,
                true,
                '{"origin": "phase2b_foreign_key_backfill"}'::jsonb,
                now()
            FROM (
                SELECT first_job_id AS job_id FROM product_source_records
                UNION
                SELECT last_job_id FROM product_source_records
            ) refs
            WHERE NOT EXISTS (
                SELECT 1 FROM import_jobs AS jobs WHERE jobs.id = refs.job_id
            )
            """
        ),
        {"admin_id": admin_id},
    )
    bind.execute(
        sa.text(
            """
            SELECT setval(
                pg_get_serial_sequence('import_jobs', 'id'),
                (SELECT MAX(id) FROM import_jobs)
            )
            """
        )
    )
    return True


def _add_source_job_foreign_keys(validated: bool) -> None:
    validity = "" if validated else " NOT VALID"
    op.execute(
        sa.text(
            f"""
            ALTER TABLE product_source_records
            ADD CONSTRAINT fk_product_source_records_first_job_id
            FOREIGN KEY (first_job_id) REFERENCES import_jobs (id)
            ON DELETE RESTRICT{validity}
            """
        )
    )
    op.execute(
        sa.text(
            f"""
            ALTER TABLE product_source_records
            ADD CONSTRAINT fk_product_source_records_last_job_id
            FOREIGN KEY (last_job_id) REFERENCES import_jobs (id)
            ON DELETE RESTRICT{validity}
            """
        )
    )
