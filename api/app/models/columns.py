from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import mapped_column


def created_at() -> datetime:
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


def updated_at() -> datetime:
    return mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
