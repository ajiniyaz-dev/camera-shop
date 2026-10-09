from pathlib import Path

from pydantic import ValidationError
import pytest

from app.config import Settings


def test_settings_require_postgresql() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="sqlite:///catalog.db",
            app_env="local",
            session_secret="test-only-secret",
        )


def test_local_environment_accepts_placeholder_secret() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://catalog:catalog@127.0.0.1:5432/catalog",
        session_secret="change-me",
        app_env="local",
        debug=False,
        public_site_url="http://localhost",
    )
    assert settings.public_site_url == "http://localhost"
    assert settings.debug is False


def test_production_rejects_placeholder_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://catalog:catalog@127.0.0.1:5432/catalog",
            session_secret="change-me-to-a-long-random-string",
            app_env="production",
            debug=False,
        )


def test_production_rejects_debug_mode() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://catalog:catalog@127.0.0.1:5432/catalog",
            session_secret="a-real-secret-value",
            app_env="production",
            debug=True,
        )


def test_core_schema_revision_is_present() -> None:
    versions = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    revisions = sorted(
        path.name
        for path in versions.glob("*.py")
        if path.name != "__init__.py"
    )
    assert revisions == ["phase2a_core_schema.py"]
