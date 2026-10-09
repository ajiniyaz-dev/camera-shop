from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Identity, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.columns import created_at, updated_at

if TYPE_CHECKING:
    from app.models.audit import AdminAuditLog
    from app.models.imports import ImportJob


class AdminUser(Base):
    __tablename__ = "admin_users"
    __table_args__ = (CheckConstraint("role = 'admin'", name="ck_admin_users_role"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()

    created_jobs: Mapped[list[ImportJob]] = relationship(
        "ImportJob",
        back_populates="creator",
        foreign_keys="ImportJob.created_by",
        passive_deletes=True,
    )
    approved_jobs: Mapped[list[ImportJob]] = relationship(
        "ImportJob",
        back_populates="approver",
        foreign_keys="ImportJob.approved_by",
        passive_deletes=True,
    )
    audit_logs: Mapped[list[AdminAuditLog]] = relationship(
        "AdminAuditLog",
        back_populates="actor",
        passive_deletes=True,
    )
