"""Server-side administrator sessions.

The raw session token and the raw CSRF token are never stored. ``token_hash``
and ``csrf_token_hash`` are HMAC-SHA256 digests keyed by ``SESSION_SECRET``.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.columns import created_at

if TYPE_CHECKING:
    from app.models.admin_user import AdminUser

_HEX_HASH = r"^[0-9a-f]{64}$"


class AdminSession(Base):
    __tablename__ = "admin_sessions"
    __table_args__ = (
        CheckConstraint(f"token_hash ~ '{_HEX_HASH}'", name="ck_admin_sessions_token_hash"),
        CheckConstraint(
            f"csrf_token_hash ~ '{_HEX_HASH}'",
            name="ck_admin_sessions_csrf_token_hash",
        ),
        CheckConstraint("expires_at > created_at", name="ck_admin_sessions_expires_at"),
        CheckConstraint(
            "revoked_at IS NULL OR revoked_at >= created_at",
            name="ck_admin_sessions_revoked_at",
        ),
        Index("uq_admin_sessions_token_hash", "token_hash", unique=True),
        Index("ix_admin_sessions_user_id", "user_id"),
        Index("ix_admin_sessions_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("admin_users.id", name="fk_admin_sessions_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    csrf_token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at()

    user: Mapped[AdminUser] = relationship(back_populates="sessions")
