from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class BusinessProfile(Base):
    __tablename__ = "business_profile"
    __table_args__ = (CheckConstraint("id = 1", name="ck_business_profile_singleton"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    public_name: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'HikVision'"))
    legal_name: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    opening_hours: Mapped[str | None] = mapped_column(Text)
    social_links: Mapped[list[dict[str, str]] | None] = mapped_column(JSONB)
    logo_object_key: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
