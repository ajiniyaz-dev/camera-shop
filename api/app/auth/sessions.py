"""Session tokens, CSRF verifiers, and auth cookies.

The browser receives the raw values once. PostgreSQL stores HMAC-SHA256
digests keyed with ``SESSION_SECRET``. Changing that secret invalidates
existing sessions.
"""

from __future__ import annotations

import hmac
import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from fastapi import Response
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import Settings
from app.models import AdminSession, AdminUser

SESSION_COOKIE_NAME = "hikvision_session"
CSRF_COOKIE_NAME = "hikvision_csrf"
CSRF_HEADER_NAME = "x-csrf-token"
COOKIE_PATH = "/api"
# The session cookie stays on /api and HttpOnly. The CSRF cookie is readable
# by the admin UI, which is served outside /api, so its path is the site root.
CSRF_COOKIE_PATH = "/"
_NO_STORE = "no-store"


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_verifier(secret: str, token: str) -> str:
    return hmac.new(secret.encode("utf-8"), token.encode("utf-8"), sha256).hexdigest()


def issue_session(db: Session, settings: Settings, user: AdminUser) -> tuple[AdminSession, str, str]:
    now = datetime.now(timezone.utc)
    session_token = new_token()
    csrf_token = new_token()
    record = AdminSession(
        user_id=user.id,
        token_hash=hash_verifier(settings.session_secret, session_token),
        csrf_token_hash=hash_verifier(settings.session_secret, csrf_token),
        expires_at=now + timedelta(seconds=settings.session_ttl_seconds),
        created_at=now,
    )
    db.add(record)
    return record, session_token, csrf_token


def find_valid_session(db: Session, settings: Settings, raw_token: str | None) -> AdminSession | None:
    if not raw_token:
        return None
    digest = hash_verifier(settings.session_secret, raw_token)
    record = db.scalar(
        select(AdminSession)
        .options(joinedload(AdminSession.user))
        .where(AdminSession.token_hash == digest)
    )
    if record is None or record.revoked_at is not None:
        return None
    now = datetime.now(timezone.utc)
    if record.expires_at <= now:
        return None
    user = record.user
    if user is None or not user.is_active:
        return None
    return record


def set_auth_cookies(response: Response, settings: Settings, session_token: str, csrf_token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.cookie_secure(),
        samesite="lax",
        path=COOKIE_PATH,
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=settings.session_ttl_seconds,
        httponly=False,
        secure=settings.cookie_secure(),
        samesite="lax",
        path=CSRF_COOKIE_PATH,
    )
    response.headers["Cache-Control"] = _NO_STORE


def clear_auth_cookies(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path=COOKIE_PATH,
        secure=settings.cookie_secure(),
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        path=CSRF_COOKIE_PATH,
        secure=settings.cookie_secure(),
        httponly=False,
        samesite="lax",
    )
    response.headers["Cache-Control"] = _NO_STORE
