import os
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.config import Settings, get_settings
from app.main import create_app
from app.models import AdminAuditLog, AdminUser, Product, ProductImage
from tests.import_builders import png_bytes

API_ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct-horse-1"
ORIGIN = "http://testserver"
ADMIN_URLS = [
    os.environ.get("PHASE2A_ADMIN_URL"),
    "postgresql+psycopg://catalog:change-me@127.0.0.1:5433/postgres",
    "postgresql+psycopg://catalog:catalog@127.0.0.1:5432/postgres",
]


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
    pytest.fail("PostgreSQL is not reachable for the disposable Phase 5 database")


def _alembic(database_url: str) -> Config:
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    return config


@pytest.fixture(scope="module")
def database_url():
    admin_url, admin_engine = _admin_engine()
    name = "catalog_phase5_test"
    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    url = admin_url.rsplit("/", 1)[0] + "/" + name
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
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin_engine.dispose()


@pytest.fixture
def engine(database_url: str):
    db_engine = create_engine(database_url)
    with db_engine.begin() as connection:
        connection.execute(
            text(
                """
                TRUNCATE TABLE
                  admin_audit_log, admin_sessions, import_assets, import_rows, import_files,
                  product_images, product_specification_translations, product_specifications,
                  product_translations, product_source_records, products, import_jobs,
                  category_translations, categories, brand_translations, brands, admin_users
                RESTART IDENTITY CASCADE
                """
            )
        )
    yield db_engine
    db_engine.dispose()


@pytest.fixture
def client(engine, database_url: str, tmp_path: Path):
    settings = Settings(
        database_url=database_url,
        session_secret="test-only-secret",
        app_env="local",
        debug=False,
        public_site_url=ORIGIN,
        media_root=str(tmp_path / "media"),
    )
    application = create_app(settings)
    with TestClient(application) as test_client:
        yield test_client
    application.state.engine.dispose()


def _seed(engine) -> None:
    db = Session(bind=engine)
    try:
        db.add(AdminUser(email="admin@example.com", password_hash=hash_password(PASSWORD), role="admin"))
        db.commit()
    finally:
        db.close()


def _auth(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": PASSWORD},
        headers={"Origin": ORIGIN},
    )
    assert response.status_code == 200
    return {"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"]}


def _product(model: str = "Hikvision NVR-9", **extra: object) -> dict[str, object]:
    body: dict[str, object] = {
        "model_display": model,
        "price": {"status": "on_request"},
        "translations": {"ru": {"description": "регистратор"}},
    }
    body.update(extra)
    return body


def test_catalog_requires_session_and_csrf(client: TestClient, engine) -> None:
    _seed(engine)
    assert client.get("/api/admin/dashboard").status_code == 401
    headers = _auth(client)
    missing = client.post("/api/admin/products", json=_product(), headers={"Origin": ORIGIN})
    assert missing.status_code == 403
    created = client.post("/api/admin/products", json=_product(), headers=headers)
    assert created.status_code == 201


def test_prices_stay_distinct_from_stock_and_zero(client: TestClient, engine) -> None:
    _seed(engine)
    headers = _auth(client)
    created = client.post("/api/admin/products", json=_product(), headers=headers)
    assert created.status_code == 201
    body = created.json()
    assert body["public_price_status"] == "on_request"
    assert body["public_price_amount"] is None
    assert body["stock_status"] == "in_stock"
    assert body["price_locked"] is True
    product_id = body["id"]
    blank = client.patch(
        f"/api/admin/products/{product_id}",
        json=_product(price={"status": "numeric", "amount": ""}),
        headers=headers,
    )
    assert blank.status_code == 422
    mixed = client.patch(
        f"/api/admin/products/{product_id}",
        json=_product(price={"status": "on_request", "amount": "0"}),
        headers=headers,
    )
    assert mixed.status_code == 422
    priced = client.patch(
        f"/api/admin/products/{product_id}",
        json=_product(price={"status": "numeric", "amount": "92.5"}, stock_status="out_of_stock"),
        headers=headers,
    )
    assert priced.status_code == 200
    assert priced.json()["public_price_amount"] == "92.50"
    assert priced.json()["public_currency"] == "USD"
    assert priced.json()["stock_status"] == "out_of_stock"
    stock_only = client.patch(
        f"/api/admin/products/{product_id}",
        json=_product(price={"status": "numeric", "amount": "92.50"}, stock_status="in_stock"),
        headers=headers,
    )
    assert stock_only.status_code == 200
    assert stock_only.json()["public_price_amount"] == "92.50"
    assert stock_only.json()["stock_status"] == "in_stock"
    again = client.post("/api/admin/products", json=_product(), headers=headers)
    assert again.status_code == 201
    assert again.json()["id"] != product_id
    listed = client.get("/api/admin/products", params={"q": "NVR-9", "page_size": 1})
    assert listed.status_code == 200
    assert listed.json()["total"] == 2
    assert len(listed.json()["products"]) == 1


def test_dashboard_profile_and_image(client: TestClient, engine) -> None:
    _seed(engine)
    headers = _auth(client)
    profile = client.get("/api/admin/profile")
    assert profile.status_code == 200
    assert profile.json()["public_name"] == "HikVision"
    assert profile.json()["phone"] is None
    assert profile.json()["email"] is None
    saved = client.patch(
        "/api/admin/profile",
        json={"public_name": "HikVision", "phone": "+998 00 000 00 00", "social_links": []},
        headers=headers,
    )
    assert saved.status_code == 200
    assert saved.json()["phone"] == "+998 00 000 00 00"
    created = client.post(
        "/api/admin/products",
        json=_product(
            catalog_status="published",
            specifications=[{"sort_order": 0, "name_ru": "Питание", "value_ru": "12 В"}],
        ),
        headers=headers,
    )
    product_id = created.json()["id"]
    uploaded = client.post(
        f"/api/admin/products/{product_id}/images",
        files={"file": ("camera.png", png_bytes(4), "image/png")},
        headers=headers,
    )
    assert uploaded.status_code == 201
    assert uploaded.json()["is_primary"] is True
    assert uploaded.json()["url"].startswith("/media/objects/")
    overview = client.get("/api/admin/dashboard")
    assert overview.status_code == 200
    assert overview.json()["products"]["published"] == 1
    assert overview.json()["products"]["total"] == 1
    db = Session(bind=engine)
    try:
        assert db.scalar(select(func.count()).select_from(ProductImage)) == 1
        audit = db.scalars(select(AdminAuditLog.action)).all()
        assert "profile_updated" in audit
        assert "image_added" in audit
        product = db.get(Product, product_id)
        assert product is not None
        assert product.public_price_amount is None
    finally:
        db.close()


def test_archive_brand_category_images_and_import_list(client: TestClient, engine) -> None:
    _seed(engine)
    headers = _auth(client)
    created = client.post("/api/admin/products", json=_product(), headers=headers)
    product_id = created.json()["id"]
    unconfirmed = client.post(f"/api/admin/products/{product_id}/archive", json={"confirm": False}, headers=headers)
    assert unconfirmed.status_code == 422
    archived = client.post(f"/api/admin/products/{product_id}/archive", json={"confirm": True}, headers=headers)
    assert archived.status_code == 200
    assert archived.json()["catalog_status"] == "archived"
    brand = client.post(
        "/api/admin/brands",
        json={"name_ru": "Hikvision", "name_uz": "Hikvision", "description_ru": "Камеры", "is_published": True},
        headers=headers,
    )
    assert brand.status_code == 201
    assert brand.json()["name_uz"] == "Hikvision"
    parent = client.post("/api/admin/categories", json={"name_ru": "Видео", "is_published": True}, headers=headers)
    assert parent.status_code == 201
    child = client.post(
        "/api/admin/categories",
        json={"name_ru": "Регистраторы", "parent_id": parent.json()["id"], "is_published": True},
        headers=headers,
    )
    assert child.status_code == 201
    cycle = client.patch(
        f"/api/admin/categories/{parent.json()['id']}",
        json={"name_ru": "Видео", "parent_id": child.json()["id"], "is_published": True},
        headers=headers,
    )
    assert cycle.status_code == 422
    first = client.post(
        f"/api/admin/products/{product_id}/images",
        files={"file": ("one.png", png_bytes(4), "image/png")},
        headers=headers,
    )
    second = client.post(
        f"/api/admin/products/{product_id}/images",
        files={"file": ("two.png", png_bytes(9), "image/png")},
        headers=headers,
    )
    assert first.json()["is_primary"] is True
    assert second.json()["is_primary"] is False
    promoted = client.patch(
        f"/api/admin/products/{product_id}/images/{second.json()['id']}",
        json={"is_primary": True},
        headers=headers,
    )
    assert promoted.status_code == 200
    assert promoted.json()["is_primary"] is True
    removed = client.delete(f"/api/admin/products/{product_id}/images/{first.json()['id']}", headers=headers)
    assert removed.status_code == 204
    listed = client.get("/api/admin/imports")
    assert listed.status_code == 200
    assert listed.json()["jobs"] == []
    rejected = client.patch(
        "/api/admin/profile",
        json={"public_name": "HikVision", "social_links": [{"label": "Site", "url": "notaurl"}]},
        headers=headers,
    )
    assert rejected.status_code == 422
