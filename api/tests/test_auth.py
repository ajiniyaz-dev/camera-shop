import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi import Depends, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import assert_active_admin, require_admin_write
from app.auth.passwords import hash_password, verify_password
from app.auth.rate_limit import LoginRateLimiter
from app.auth.sessions import hash_verifier, new_token
from app.cli.create_admin import main
from app.config import Settings, get_settings
from app.main import create_app
from app.models import AdminSession, AdminUser

API_ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct-horse-1"
OTHER_PASSWORD = "another-test-password"
ADMIN_URLS = [
    os.environ.get("PHASE2A_ADMIN_URL"),
    "postgresql+psycopg://catalog:change-me@127.0.0.1:5433/postgres",
    "postgresql+psycopg://catalog:catalog@127.0.0.1:5432/postgres",
]
ORIGIN = {"Origin": "http://testserver"}


def _connect(url: str):
    engine = create_engine(url, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 3})
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        engine.dispose()
        return None
    return engine


def _admin_engine():
    for url in ADMIN_URLS:
        if not url:
            continue
        engine = _connect(url)
        if engine is not None:
            return url, engine
    pytest.fail("PostgreSQL is not reachable for the disposable Phase 3 database")


def _alembic(database_url: str) -> Config:
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    return config


def _recreate(admin_engine, database_name: str, admin_url: str) -> str:
    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    return admin_url.rsplit("/", 1)[0] + "/" + database_name


def _settings(database_url: str, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": database_url,
        "session_secret": "test-only-secret",
        "app_env": "local",
        "debug": False,
        "public_site_url": "http://testserver",
    }
    values.update(overrides)
    return Settings(**values)


@pytest.fixture(scope="module")
def database_url():
    admin_url, admin_engine = _admin_engine()
    url = _recreate(admin_engine, "catalog_phase3_test", admin_url)
    previous = os.environ.get("DATABASE_URL")
    try:
        command.upgrade(_alembic(url), "head")
        yield url
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()
        with admin_engine.connect() as connection:
            connection.execute(text('DROP DATABASE IF EXISTS "catalog_phase3_test" WITH (FORCE)'))
        admin_engine.dispose()


@pytest.fixture
def engine(database_url: str):
    db_engine = create_engine(database_url)
    with db_engine.begin() as connection:
        connection.execute(
            text("TRUNCATE admin_sessions, admin_audit_log, admin_users RESTART IDENTITY CASCADE")
        )
    yield db_engine
    db_engine.dispose()


@pytest.fixture
def client(engine, database_url: str):
    application = create_app(_settings(database_url))
    with TestClient(application) as test_client:
        yield test_client
    application.state.engine.dispose()


def _seed(engine, *, email: str = "admin@example.com", active: bool = True) -> None:
    db = Session(bind=engine)
    try:
        db.add(
            AdminUser(
                email=email,
                password_hash=hash_password(PASSWORD),
                role="admin",
                is_active=active,
            )
        )
        db.commit()
    finally:
        db.close()


def _login(client: TestClient, email: str = "admin@example.com", password: str = PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password}, headers=ORIGIN)


def _csrf_headers(token: str, origin: str = "http://testserver") -> dict[str, str]:
    return {"Origin": origin, "X-CSRF-Token": token}


def test_non_admin_role_is_forbidden() -> None:
    user = AdminUser(email="staff@example.com", password_hash="stored-hash", role="editor", is_active=True)
    with pytest.raises(HTTPException) as caught:
        assert_active_admin(user)
    assert caught.value.status_code == 403


def test_login_success_sets_cookies_and_hides_the_hash(engine, client: TestClient) -> None:
    _seed(engine)
    response = _login(client, "Admin@Example.com")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "admin@example.com"
    assert body["role"] == "admin"
    assert "csrf_token" in body
    assert "password_hash" not in body
    assert "$argon2" not in response.text
    cookies = response.headers.get_list("set-cookie")
    session_cookie = next(item for item in cookies if item.startswith("hikvision_session="))
    csrf_cookie = next(item for item in cookies if item.startswith("hikvision_csrf="))
    assert "httponly" in session_cookie.lower()
    assert "samesite=lax" in session_cookie.lower()
    assert "path=/api" in session_cookie.lower()
    assert "secure" not in session_cookie.lower()
    assert "httponly" not in csrf_cookie.lower()
    assert "path=/" in csrf_cookie.lower()
    assert "path=/api" not in csrf_cookie.lower()
    with engine.connect() as connection:
        stored = connection.execute(text("SELECT token_hash, csrf_token_hash FROM admin_sessions")).one()
    raw_session = client.cookies.get("hikvision_session")
    assert raw_session
    assert stored.token_hash != raw_session
    assert stored.token_hash == hash_verifier("test-only-secret", raw_session)
    assert stored.csrf_token_hash == hash_verifier("test-only-secret", body["csrf_token"])
    assert PASSWORD not in response.text


def test_unknown_email_and_bad_password_look_the_same(engine, client: TestClient) -> None:
    _seed(engine)
    unknown = _login(client, "missing@example.com", OTHER_PASSWORD)
    wrong = _login(client, "admin@example.com", OTHER_PASSWORD)
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json() == {"detail": "The email or password is incorrect."}
    assert PASSWORD not in unknown.text
    assert OTHER_PASSWORD not in unknown.text
    assert "$argon2" not in unknown.text
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT action, actor_id, detail::text FROM admin_audit_log ORDER BY id")
        ).all()
        sessions = connection.execute(text("SELECT count(*) FROM admin_sessions")).scalar_one()
    assert sessions == 0
    assert rows[0].actor_id is None
    assert rows[1].actor_id is not None
    assert all(row.action == "login_failure" for row in rows)
    assert all("password" not in row[2] for row in rows)


def test_inactive_administrator_is_rejected(engine, client: TestClient) -> None:
    _seed(engine, active=False)
    response = _login(client)
    assert response.status_code == 401
    assert response.json()["detail"] == "The email or password is incorrect."
    assert "set-cookie" not in response.headers


def test_me_requires_a_valid_session_and_logout_revokes_it(engine, client: TestClient) -> None:
    _seed(engine)
    assert client.get("/api/auth/me").status_code == 401
    logged_in = _login(client)
    csrf = logged_in.json()["csrf_token"]
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert set(me.json()) == {"id", "email", "role"}
    assert "$argon2" not in me.text
    missing = client.post("/api/auth/logout", headers=ORIGIN)
    assert missing.status_code == 403
    wrong = client.post("/api/auth/logout", headers=_csrf_headers("not-the-token"))
    assert wrong.status_code == 403
    foreign = client.post("/api/auth/logout", headers=_csrf_headers(csrf, "http://evil.example"))
    assert foreign.status_code == 403
    assert client.get("/api/auth/me").status_code == 200
    session_token = client.cookies.get("hikvision_session")
    logged_out = client.post("/api/auth/logout", headers=_csrf_headers(csrf))
    assert logged_out.status_code == 204
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.set("hikvision_session", session_token)
    assert client.get("/api/auth/me").status_code == 401


def test_expired_and_revoked_sessions_are_rejected(engine, client: TestClient, database_url: str) -> None:
    _seed(engine)
    db = Session(bind=engine)
    try:
        user_id = db.scalar(text("SELECT id FROM admin_users"))
        now = datetime.now(timezone.utc)
        expired = new_token()
        revoked = new_token()
        db.add(
            AdminSession(
                user_id=user_id,
                token_hash=hash_verifier("test-only-secret", expired),
                csrf_token_hash=hash_verifier("test-only-secret", new_token()),
                created_at=now - timedelta(hours=2),
                expires_at=now - timedelta(minutes=1),
            )
        )
        db.add(
            AdminSession(
                user_id=user_id,
                token_hash=hash_verifier("test-only-secret", revoked),
                csrf_token_hash=hash_verifier("test-only-secret", new_token()),
                created_at=now,
                expires_at=now + timedelta(hours=1),
                revoked_at=now,
            )
        )
        db.commit()
    finally:
        db.close()
    client.cookies.set("hikvision_session", expired)
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.set("hikvision_session", revoked)
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.set("hikvision_session", "not-a-real-session")
    assert client.get("/api/auth/me").status_code == 401
    assert database_url.startswith("postgresql")


def test_deactivating_an_administrator_rejects_the_existing_session(engine, client: TestClient) -> None:
    _seed(engine)
    assert _login(client).status_code == 200
    with engine.begin() as connection:
        connection.execute(text("UPDATE admin_users SET is_active = false"))
    assert client.get("/api/auth/me").status_code == 401


def test_production_session_cookie_is_secure(engine, database_url: str) -> None:
    _seed(engine)
    application = create_app(_settings(database_url, app_env="production"))
    try:
        with TestClient(application) as production_client:
            response = _login(production_client)
    finally:
        application.state.engine.dispose()
    assert response.status_code == 200
    session_cookie = next(
        item
        for item in response.headers.get_list("set-cookie")
        if item.startswith("hikvision_session=")
    )
    assert "secure" in session_cookie.lower()
    assert "httponly" in session_cookie.lower()


def test_login_rate_limit_then_allows_again_after_the_window(engine, database_url: str) -> None:
    _seed(engine)
    application = create_app(
        _settings(database_url, login_rate_limit_max=2, login_rate_limit_window_seconds=60)
    )
    clock = {"now": 1_000.0}
    application.state.login_rate_limiter.clock = lambda: clock["now"]
    try:
        with TestClient(application) as limited:
            first = _login(limited, password=OTHER_PASSWORD)
            second = _login(limited, "missing@example.com", OTHER_PASSWORD)
            blocked = _login(limited)
            assert first.status_code == second.status_code == 401
            assert first.json() == second.json()
            assert blocked.status_code == 429
            assert blocked.json() == {"detail": "Too many login attempts. Try again later."}
            assert "admin@example.com" not in blocked.text
            clock["now"] += 60
            allowed = _login(limited)
            assert allowed.status_code == 200
    finally:
        application.state.engine.dispose()


def test_forwarded_headers_do_not_choose_the_limiter_key_unless_trusted(engine, database_url: str) -> None:
    _seed(engine)
    direct = create_app(_settings(database_url, login_rate_limit_max=1, trust_proxy=False))
    try:
        with TestClient(direct) as client:
            spoofed = {
                "Origin": "http://testserver",
                "X-Forwarded-For": "203.0.113.5",
                "X-Real-IP": "203.0.113.9",
            }
            assert client.post(
                "/api/auth/login",
                json={"email": "admin@example.com", "password": OTHER_PASSWORD},
                headers=spoofed,
            ).status_code == 401
            blocked = client.post(
                "/api/auth/login",
                json={"email": "missing@example.com", "password": OTHER_PASSWORD},
                headers={**spoofed, "X-Forwarded-For": "198.51.100.20", "X-Real-IP": "198.51.100.21"},
            )
            assert blocked.status_code == 429
    finally:
        direct.state.engine.dispose()

    trusted = create_app(_settings(database_url, login_rate_limit_max=1, trust_proxy=True))
    try:
        with TestClient(trusted) as client:
            first = client.post(
                "/api/auth/login",
                json={"email": "admin@example.com", "password": OTHER_PASSWORD},
                headers={"Origin": "http://testserver", "X-Real-IP": "203.0.113.9", "X-Forwarded-For": "198.51.100.8"},
            )
            assert first.status_code == 401
            forwarded_only = client.post(
                "/api/auth/login",
                json={"email": "admin@example.com", "password": OTHER_PASSWORD},
                headers={"Origin": "http://testserver", "X-Real-IP": "203.0.113.9", "X-Forwarded-For": "198.51.100.50"},
            )
            assert forwarded_only.status_code == 429
            other_proxy_client = client.post(
                "/api/auth/login",
                json={"email": "admin@example.com", "password": OTHER_PASSWORD},
                headers={"Origin": "http://testserver", "X-Real-IP": "203.0.113.10"},
            )
            assert other_proxy_client.status_code == 401
    finally:
        trusted.state.engine.dispose()


def test_write_dependency_rejects_missing_session_and_csrf(engine, database_url: str) -> None:
    _seed(engine)
    application = create_app(_settings(database_url))

    @application.post("/api/admin/probe")
    def probe(_user: AdminUser = Depends(require_admin_write)) -> dict[str, bool]:
        return {"ok": True}

    try:
        with TestClient(application) as client:
            assert client.post("/api/admin/probe", headers=ORIGIN).status_code == 401
            logged_in = _login(client)
            csrf = logged_in.json()["csrf_token"]
            assert client.post("/api/admin/probe", headers=ORIGIN).status_code == 403
            accepted = client.post("/api/admin/probe", headers=_csrf_headers(csrf))
            assert accepted.status_code == 200
            assert accepted.json() == {"ok": True}
    finally:
        application.state.engine.dispose()


def test_deleting_an_administrator_removes_sessions(engine, client: TestClient) -> None:
    _seed(engine)
    assert _login(client).status_code == 200
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM admin_users"))
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM admin_audit_log"))
        connection.execute(text("DELETE FROM admin_users"))
        remaining = connection.execute(text("SELECT count(*) FROM admin_sessions")).scalar_one()
    assert remaining == 0
    assert client.get("/api/auth/me").status_code == 401


def test_rate_limiter_drops_idle_keys() -> None:
    clock = {"now": 0.0}
    limiter = LoginRateLimiter(max_attempts=1, window_seconds=10, max_keys=1, clock=lambda: clock["now"])
    limiter.record_failure("10.0.0.1")
    limiter.record_failure("10.0.0.2")
    assert limiter.is_limited("10.0.0.2") is True
    assert "10.0.0.1" not in limiter._failures
    clock["now"] = 10
    assert limiter.is_limited("10.0.0.2") is False


def test_invalid_login_body_does_not_echo_the_password(client: TestClient) -> None:
    secret = "short"
    response = client.post("/api/auth/login", json={"email": "not-an-email", "password": secret})
    assert response.status_code == 422
    assert response.json() == {"detail": "The login request is invalid."}
    assert secret not in response.text


def test_first_administrator_command_hashes_the_password_and_runs_once(engine, database_url: str, capsys) -> None:
    previous = {
        "DATABASE_URL": os.environ.get("DATABASE_URL"),
        "SESSION_SECRET": os.environ.get("SESSION_SECRET"),
        "APP_ENV": os.environ.get("APP_ENV"),
    }
    os.environ["DATABASE_URL"] = database_url
    os.environ["SESSION_SECRET"] = "test-only-secret"
    os.environ["APP_ENV"] = "local"
    get_settings.cache_clear()
    prompts = iter([PASSWORD, PASSWORD])
    try:
        assert main(["--password", PASSWORD]) == 2
        assert main(["Admin@Example.com"], password_reader=lambda _prompt: next(prompts)) == 0
        captured = capsys.readouterr()
        assert PASSWORD not in captured.out
        assert PASSWORD not in captured.err
        assert "admin@example.com" in captured.out
        with engine.connect() as connection:
            row = connection.execute(text("SELECT email, password_hash, role FROM admin_users")).one()
        assert row.email == "admin@example.com"
        assert row.role == "admin"
        assert row.password_hash != PASSWORD
        assert verify_password(row.password_hash, PASSWORD)
        assert row.password_hash.startswith("$argon2id$")
        again = iter([OTHER_PASSWORD, OTHER_PASSWORD])
        assert main(["second@example.com"], password_reader=lambda _prompt: next(again)) == 1
        mismatch = iter([PASSWORD, OTHER_PASSWORD])
        assert main(["third@example.com"], password_reader=lambda _prompt: next(mismatch)) == 1
        short = iter(["short-pass", "short-pass"])
        assert main(["fourth@example.com"], password_reader=lambda _prompt: next(short)) == 1
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()


def test_upgrade_preserves_existing_admin_and_catalog_rows() -> None:
    admin_url, admin_engine = _admin_engine()
    database_url = _recreate(admin_engine, "catalog_phase3_upgrade", admin_url)
    previous = os.environ.get("DATABASE_URL")
    config = _alembic(database_url)
    db_engine = create_engine(database_url)
    try:
        command.upgrade(config, "phase2b_import")
        password_hash = hash_password(PASSWORD)
        with db_engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO admin_users (email, password_hash, role)
                    VALUES ('preserved@example.com', :password_hash, 'admin')
                    """
                ),
                {"password_hash": password_hash},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO products (
                        product_kind, model_raw, model_display, model_normalized,
                        public_price_status, slug, catalog_status
                    )
                    VALUES (
                        'product', 'preserved', 'preserved', 'preserved',
                        'on_request', 'preserved-admin-product', 'draft'
                    )
                    """
                )
            )
        command.upgrade(config, "head")
        with db_engine.connect() as connection:
            admin = connection.execute(
                text("SELECT email, password_hash, is_active FROM admin_users")
            ).one()
            product = connection.execute(
                text("SELECT slug, public_price_status FROM products")
            ).one()
            version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            sessions = connection.execute(
                text(
                    """
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'admin_sessions'
                    """
                )
            ).first()
        assert admin.email == "preserved@example.com"
        assert admin.password_hash == password_hash
        assert admin.is_active is True
        assert product.slug == "preserved-admin-product"
        assert product.public_price_status == "on_request"
        assert sessions is not None
        assert version == "phase3_admin_sessions"
        command.downgrade(config, "phase2b_import")
        with db_engine.connect() as connection:
            names = {
                row[0]
                for row in connection.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                )
            }
            surviving = connection.execute(text("SELECT email FROM admin_users")).scalar_one()
            downgraded = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert "admin_sessions" not in names
        assert "admin_users" in names
        assert "products" in names
        assert surviving == "preserved@example.com"
        assert downgraded == "phase2b_import"
    finally:
        db_engine.dispose()
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()
        with admin_engine.connect() as connection:
            connection.execute(text('DROP DATABASE IF EXISTS "catalog_phase3_upgrade" WITH (FORCE)'))
        admin_engine.dispose()
