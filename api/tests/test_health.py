import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

API_ROOT = Path(__file__).resolve().parents[1]

_LOCAL_URL = "postgresql+psycopg://catalog:catalog@127.0.0.1:5432/catalog"


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": _LOCAL_URL,
        "session_secret": "test-only-secret",
        "app_env": "local",
        "debug": False,
    }
    values.update(overrides)
    return Settings(**values)


def test_health_reports_database_connectivity(monkeypatch) -> None:
    called = {"count": 0}

    def fake_check(engine: object) -> None:
        called["count"] += 1
        assert engine is not None

    monkeypatch.setattr("app.health.check_database", fake_check)
    application = create_app(_settings())
    try:
        with TestClient(application) as client:
            response = client.get("/api/health")
    finally:
        application.state.engine.dispose()

    assert called["count"] == 1
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert "postgresql" not in response.text.lower()
    assert "session_secret" not in response.text.lower()


def test_health_fails_when_database_is_unreachable() -> None:
    application = create_app(
        _settings(
            database_url="postgresql+psycopg://catalog:wrong@127.0.0.1:1/catalog",
        )
    )
    try:
        with TestClient(application) as client:
            response = client.get("/api/health")
    finally:
        application.state.engine.dispose()

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unavailable"}
    assert "wrong" not in response.text
    assert "postgresql" not in response.text.lower()
    assert "127.0.0.1" not in response.text


def test_interactive_docs_are_disabled_unless_debug() -> None:
    application = create_app(_settings(debug=False))
    try:
        with TestClient(application) as client:
            assert client.get("/docs").status_code == 404
            assert client.get("/openapi.json").status_code == 404
            assert client.get("/health").status_code == 404
    finally:
        application.state.engine.dispose()


def test_interactive_docs_are_available_in_debug() -> None:
    application = create_app(_settings(debug=True))
    try:
        with TestClient(application) as client:
            assert client.get("/openapi.json").status_code == 200
    finally:
        application.state.engine.dispose()


def test_alembic_heads_load_without_applying_migrations() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "heads"],
        cwd=API_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
