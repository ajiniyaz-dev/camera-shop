"""Attach verified source-backed primaries for six imageless products.

Revision ID: source_backed_missing_primaries
Revises: approved_uz_en_product_names
Create Date: 2026-10-19

Slug-keyed data patch for products 37, 110, 111, 184, 200, and 383. Each
already has a photo-column ``linked_high`` import asset; this only creates the
missing ``product_images`` rows. Skips products that already have images.
Does not run workbook import/apply.
"""

from pathlib import Path
from typing import Sequence, Union

from alembic import op

from app.config import get_settings
from app.data.source_backed_missing_primaries import (
    apply_source_backed_missing_primaries,
    revert_source_backed_missing_primaries,
)

revision: str = "source_backed_missing_primaries"
down_revision: Union[str, Sequence[str], None] = "approved_uz_en_product_names"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    media_root = Path(get_settings().media_root)
    apply_source_backed_missing_primaries(op.get_bind(), media_root=media_root)


def downgrade() -> None:
    revert_source_backed_missing_primaries(op.get_bind())
