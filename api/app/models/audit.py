"""Append-only admin audit rows. The application must not update or delete them.

``actor_id`` is nullable so a failed login can be recorded when the email does
not match an administrator. ``detail`` is a before/after summary. A check
rejects JSON keys that would store a password, secret, or session token.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Identity, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.columns import created_at

if TYPE_CHECKING:
    from app.models.admin_user import AdminUser

DETAIL_SECRET_CHECK = """
(
  detail IS NULL
  OR (
    jsonb_typeof(detail) = 'object'
    AND detail::text !~* '"(password(_hash)?|secret|session_token|token)"[[:space:]]*:'
  )
)
"""


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"
    __table_args__ = (
        CheckConstraint("length(btrim(action)) > 0", name="ck_admin_audit_log_action"),
        CheckConstraint(
            "entity_id IS NULL OR entity_type IS NOT NULL",
            name="ck_admin_audit_log_entity",
        ),
        CheckConstraint(DETAIL_SECRET_CHECK, name="ck_admin_audit_log_detail"),
        Index("ix_admin_audit_log_actor_id", "actor_id"),
        Index("ix_admin_audit_log_created_at", "created_at"),
        Index("ix_admin_audit_log_entity", "entity_type", "entity_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", name="fk_admin_audit_log_actor_id", ondelete="RESTRICT")
    )
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(Text)
    entity_id: Mapped[int | None] = mapped_column(BigInteger)
    detail: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at()

    actor: Mapped[AdminUser | None] = relationship(
        "AdminUser",
        back_populates="audit_logs",
        passive_deletes=True,
    )
