"""Argon2id password hashing. Plaintext passwords are not stored or logged."""

from __future__ import annotations

import secrets
import threading

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()
_dummy_lock = threading.Lock()
_dummy_hash: str | None = None

MINIMUM_PASSWORD_LENGTH = 12
MAXIMUM_PASSWORD_LENGTH = 1024


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def verify_against_dummy(password: str) -> None:
    """Spend an Argon2 verification when the account does not exist.

    This keeps unknown-email failures from returning faster than a real check.
    """

    global _dummy_hash
    with _dummy_lock:
        if _dummy_hash is None:
            _dummy_hash = hash_password(secrets.token_urlsafe(32))
        dummy = _dummy_hash
    verify_password(dummy, password)


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    if len(email) > 254 or email.count("@") != 1 or any(char.isspace() for char in email):
        raise ValueError("Enter a valid email address.")
    local, _, domain = email.partition("@")
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise ValueError("Enter a valid email address.")
    return email


def validate_new_password(password: str) -> None:
    if len(password) < MINIMUM_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MINIMUM_PASSWORD_LENGTH} characters.")
    if len(password) > MAXIMUM_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at most {MAXIMUM_PASSWORD_LENGTH} characters.")
