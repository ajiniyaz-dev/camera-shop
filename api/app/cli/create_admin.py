"""Create the first administrator.

The password is read from an interactive prompt. Do not pass it as an argument,
an environment variable, or a file that is committed.

    python -m app.cli.create_admin admin@example.com

The command refuses to run when any administrator already exists.
"""

from __future__ import annotations

import getpass
import sys
from collections.abc import Callable

from pydantic import ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password, normalize_email, validate_new_password
from app.config import get_settings
from app.db import create_db_engine, create_session_factory
from app.models import AdminUser


class FirstAdminError(Exception):
    pass


def create_first_admin(db: Session, email: str, password: str) -> AdminUser:
    normalized = normalize_email(email)
    validate_new_password(password)
    db.execute(text("LOCK TABLE admin_users IN EXCLUSIVE MODE"))
    existing = db.scalar(select(func.count()).select_from(AdminUser))
    if existing:
        raise FirstAdminError("An administrator already exists.")
    admin = AdminUser(
        email=normalized,
        password_hash=hash_password(password),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    return admin


def prompt_password(reader: Callable[[str], str] = getpass.getpass) -> str:
    first = reader("Password: ")
    second = reader("Repeat password: ")
    if first != second:
        raise FirstAdminError("Passwords do not match.")
    try:
        validate_new_password(first)
    except ValueError as exc:
        raise FirstAdminError(str(exc)) from exc
    return first


def main(argv: list[str] | None = None, password_reader: Callable[[str], str] = getpass.getpass) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if any(arg == "--password" or arg.startswith("--password=") for arg in args):
        print("Do not pass the password on the command line.", file=sys.stderr)
        return 2
    if len(args) > 1:
        print("Usage: python -m app.cli.create_admin [email]", file=sys.stderr)
        return 2
    try:
        email = args[0] if args else input("Email: ")
        password = prompt_password(password_reader)
        settings = get_settings()
    except FirstAdminError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ValidationError:
        print("Configuration is invalid. Check DATABASE_URL and SESSION_SECRET.", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    engine = create_db_engine(settings.database_url)
    db = create_session_factory(engine)()
    try:
        admin = create_first_admin(db, email, password)
    except FirstAdminError as exc:
        db.rollback()
        print(str(exc), file=sys.stderr)
        return 1
    except ValueError as exc:
        db.rollback()
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        db.close()
        engine.dispose()
    print(f"Created administrator {admin.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
