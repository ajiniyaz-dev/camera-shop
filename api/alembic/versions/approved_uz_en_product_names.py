"""Approved Uzbek/English product localized names.

Revision ID: approved_uz_en_product_names
Revises: phase3_admin_sessions
Create Date: 2026-10-19

Idempotent data patch for the 17 high-confidence products from
``docs/translation-approval-list.md``. Matches products by stable slug.
Does not invent names for unresolved products. Does not overwrite a
non-null ``localized_name`` that differs from the approved value.
Descriptions, Russian names, models, prices, images, and option labels
are untouched.
"""

from typing import Sequence, Union

from alembic import op

from app.data.approved_uz_en_product_names import (
    apply_approved_uz_en_product_names,
    revert_approved_uz_en_product_names,
)

revision: str = "approved_uz_en_product_names"
down_revision: Union[str, Sequence[str], None] = "phase3_admin_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    apply_approved_uz_en_product_names(op.get_bind())


def downgrade() -> None:
    revert_approved_uz_en_product_names(op.get_bind())
