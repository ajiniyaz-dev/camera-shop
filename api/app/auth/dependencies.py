"""Backend authentication dependencies. Frontend checks are not a substitute."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth.csrf import assert_csrf
from app.auth.sessions import SESSION_COOKIE_NAME, find_valid_session
from app.config import Settings
from app.models import AdminSession, AdminUser

AUTH_REQUIRED = "Authentication is required."
ADMIN_REQUIRED = "Administrator permission is required."


def get_settings_from_request(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Iterator[Session]:
    db = request.app.state.session_factory()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def load_session(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> AdminSession | None:
    return find_valid_session(db, settings, request.cookies.get(SESSION_COOKIE_NAME))


def require_session(
    record: AdminSession | None = Depends(load_session),
) -> AdminSession:
    if record is None:
        raise HTTPException(status_code=401, detail=AUTH_REQUIRED)
    return record


def assert_active_admin(user: AdminUser) -> None:
    if not user.is_active:
        raise HTTPException(status_code=401, detail=AUTH_REQUIRED)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail=ADMIN_REQUIRED)


def require_admin(record: AdminSession = Depends(require_session)) -> AdminUser:
    """Use on authenticated reads. Write routes must use ``require_admin_write``."""

    assert_active_admin(record.user)
    return record.user


def require_admin_write(
    request: Request,
    record: AdminSession = Depends(require_session),
    settings: Settings = Depends(get_settings_from_request),
) -> AdminUser:
    """Authenticated write: active administrator, CSRF token, and matching origin."""

    assert_active_admin(record.user)
    assert_csrf(request, settings, record)
    return record.user
