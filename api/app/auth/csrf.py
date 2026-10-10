"""CSRF checks for cookie-authenticated writes.

A state-changing request must present the login CSRF token in both the
``hikvision_csrf`` cookie and the ``X-CSRF-Token`` header, and its origin must
match this site. The token is rotated when a new session is created and is
discarded on logout, expiry, or revocation.
"""

from __future__ import annotations

import hmac
from urllib.parse import urlsplit

from fastapi import HTTPException, Request, Response

from app.config import Settings
from app.auth.sessions import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, hash_verifier
from app.models import AdminSession

CSRF_FAILURE = "CSRF validation failed."


def assert_csrf(request: Request, settings: Settings, record: AdminSession) -> None:
    header = request.headers.get(CSRF_HEADER_NAME, "")
    cookie = request.cookies.get(CSRF_COOKIE_NAME, "")
    if not header or not cookie or not hmac.compare_digest(header, cookie):
        raise HTTPException(status_code=403, detail=CSRF_FAILURE)
    expected = hash_verifier(settings.session_secret, header)
    if not hmac.compare_digest(expected, record.csrf_token_hash):
        raise HTTPException(status_code=403, detail=CSRF_FAILURE)
    _assert_origin(request, settings)


def _assert_origin(request: Request, settings: Settings) -> None:
    supplied = _supplied_origin(request)
    if supplied is None or supplied not in _allowed_origins(request, settings):
        raise HTTPException(status_code=403, detail=CSRF_FAILURE)


def _supplied_origin(request: Request) -> str | None:
    origin = request.headers.get("origin")
    if origin:
        return _origin_of(origin)
    return _origin_of(request.headers.get("referer", ""))


def _allowed_origins(request: Request, settings: Settings) -> set[str]:
    allowed: set[str] = set()
    site = _origin_of(settings.public_site_url)
    if site is not None:
        allowed.add(site)
    host = request.headers.get("host")
    if host:
        if settings.trust_proxy:
            forwarded = request.headers.get("x-forwarded-proto", request.url.scheme)
            scheme = forwarded.split(",", 1)[0].strip().lower()
        else:
            scheme = request.url.scheme
        if scheme in {"http", "https"}:
            allowed.add(f"{scheme}://{host}")
    return allowed


def _origin_of(value: str) -> str | None:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def client_address(request: Request, settings: Settings) -> str:
    if settings.trust_proxy:
        real_ip = request.headers.get("x-real-ip", "").strip()
        if real_ip:
            return real_ip[:128]
    if request.client is None or not request.client.host:
        return "unknown"
    return request.client.host


def no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
