"""Server-side administrator sessions.

Revision ID: phase3_admin_sessions
Revises: phase2b_import
Create Date: 2026-10-10

The Phase 2A and Phase 2B migrations are unchanged. This revision adds
``admin_sessions`` only. ``csrf_token_hash`` stores an HMAC of the CSRF token
so the raw token is not kept in the database.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "phase3_admin_sessions"
down_revision: Union[str, Sequence[str], None] = "phase2b_import"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_HEX_HASH = r"^[0-9a-f]{64}$"


def upgrade() -> None:
    op.create_table(
        "admin_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("csrf_token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["admin_users.id"],
            name="fk_admin_sessions_user_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(f"token_hash ~ '{_HEX_HASH}'", name="ck_admin_sessions_token_hash"),
        sa.CheckConstraint(
            f"csrf_token_hash ~ '{_HEX_HASH}'",
            name="ck_admin_sessions_csrf_token_hash",
        ),
        sa.CheckConstraint("expires_at > created_at", name="ck_admin_sessions_expires_at"),
        sa.CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= created_at",
            name="ck_admin_sessions_revoked_at",
        ),
    )
    op.create_index("uq_admin_sessions_token_hash", "admin_sessions", ["token_hash"], unique=True)
    op.create_index("ix_admin_sessions_user_id", "admin_sessions", ["user_id"])
    op.create_index("ix_admin_sessions_expires_at", "admin_sessions", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_admin_sessions_expires_at", table_name="admin_sessions")
    op.drop_index("ix_admin_sessions_user_id", table_name="admin_sessions")
    op.drop_index("uq_admin_sessions_token_hash", table_name="admin_sessions")
    op.drop_table("admin_sessions")
