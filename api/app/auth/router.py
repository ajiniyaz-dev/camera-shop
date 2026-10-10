"""Administrator login, logout, and the current-session endpoint."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.auth.csrf import assert_csrf, client_address, no_store
from app.auth.dependencies import get_db, get_settings_from_request, require_admin
from app.auth.passwords import (
    MAXIMUM_PASSWORD_LENGTH,
    normalize_email,
    verify_against_dummy,
    verify_password,
)
from app.auth.sessions import (
    SESSION_COOKIE_NAME,
    clear_auth_cookies,
    find_valid_session,
    issue_session,
    set_auth_cookies,
)
from app.models import AdminAuditLog, AdminUser

router = APIRouter(prefix="/api/auth", tags=["auth"])

LOGIN_FAILURE = "The email or password is incorrect."
RATE_LIMITED = "Too many login attempts. Try again later."
_NO_STORE = {"Cache-Control": "no-store"}


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=MAXIMUM_PASSWORD_LENGTH)

    @field_validator("email")
    @classmethod
    def email_is_usable(cls, value: str) -> str:
        return normalize_email(value)


class AdminStatus(BaseModel):
    id: int
    email: str
    role: str


def _status(user: AdminUser) -> dict[str, object]:
    return AdminStatus(id=user.id, email=user.email, role=user.role).model_dump()


def _audit(
    db: Session,
    *,
    action: str,
    request: Request,
    settings: Settings,
    user: AdminUser | None,
) -> None:
    db.add(
        AdminAuditLog(
            actor_id=None if user is None else user.id,
            action=action,
            entity_type=None if user is None else "admin_user",
            entity_id=None if user is None else user.id,
            detail={"result": "success" if action == "login_success" else "failure"},
            ip_address=client_address(request, settings),
        )
    )


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> JSONResponse:
    limiter = request.app.state.login_rate_limiter
    address = client_address(request, settings)
    if limiter.is_limited(address):
        return JSONResponse(status_code=429, content={"detail": RATE_LIMITED}, headers=_NO_STORE)

    user = db.scalar(select(AdminUser).where(AdminUser.email == payload.email))
    password_ok = False
    if user is None:
        verify_against_dummy(payload.password)
    else:
        password_ok = verify_password(user.password_hash, payload.password)

    if user is None or not password_ok or not user.is_active:
        _audit(db, action="login_failure", request=request, settings=settings, user=user)
        db.commit()
        limiter.record_failure(address)
        return JSONResponse(status_code=401, content={"detail": LOGIN_FAILURE}, headers=_NO_STORE)

    _record, session_token, csrf_token = issue_session(db, settings, user)
    user.last_login_at = datetime.now(timezone.utc)
    _audit(db, action="login_success", request=request, settings=settings, user=user)
    db.commit()
    response = JSONResponse(
        status_code=200,
        content={**_status(user), "csrf_token": csrf_token},
        headers=_NO_STORE,
    )
    set_auth_cookies(response, settings, session_token, csrf_token)
    return response


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> Response:
    record = find_valid_session(db, settings, request.cookies.get(SESSION_COOKIE_NAME))
    if record is None:
        clear_auth_cookies(response, settings)
        return Response(status_code=204, headers=_NO_STORE)
    try:
        assert_csrf(request, settings, record)
    except HTTPException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=_NO_STORE,
        )
    record.revoked_at = datetime.now(timezone.utc)
    db.commit()
    clear_auth_cookies(response, settings)
    return Response(status_code=204, headers=_NO_STORE)


@router.get("/me", response_model=AdminStatus)
def me(response: Response, user: AdminUser = Depends(require_admin)) -> AdminStatus:
    no_store(response)
    return AdminStatus(id=user.id, email=user.email, role=user.role)
