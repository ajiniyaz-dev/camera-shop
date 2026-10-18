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
from app.models import (
    AdminAuditLog,
    AdminUser,
    ImportAsset,
    ImportFile,
    ImportJob,
    ImportRow,
    Product,
    ProductImage,
    ProductSourceRecord,
)
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


def test_product_search_matches_exact_id_and_model(client: TestClient, engine) -> None:
    _seed(engine)
    headers = _auth(client)
    alpha = client.post("/api/admin/products", json=_product("Alpha Camera"), headers=headers)
    beta = client.post("/api/admin/products", json=_product("Beta Recorder"), headers=headers)
    numbered = client.post("/api/admin/products", json=_product("Series 2047"), headers=headers)
    assert alpha.status_code == beta.status_code == numbered.status_code == 201
    alpha_id = alpha.json()["id"]
    beta_id = beta.json()["id"]

    by_model = client.get("/api/admin/products", params={"q": "Recorder"})
    assert by_model.status_code == 200
    assert by_model.json()["total"] == 1
    assert [item["id"] for item in by_model.json()["products"]] == [beta_id]

    by_id = client.get("/api/admin/products", params={"q": str(alpha_id), "catalog_status": "draft"})
    assert by_id.status_code == 200
    assert by_id.json()["total"] == 1
    assert by_id.json()["products"][0]["id"] == alpha_id
    assert by_id.json()["products"][0]["model_display"] == "Alpha Camera"

    hidden_by_status = client.get(
        "/api/admin/products",
        params={"q": str(alpha_id), "catalog_status": "published"},
    )
    assert hidden_by_status.json()["total"] == 0

    by_fragment = client.get("/api/admin/products", params={"q": "2047"})
    assert by_fragment.json()["total"] == 1
    assert by_fragment.json()["products"][0]["id"] == numbered.json()["id"]

    padded = client.get("/api/admin/products", params={"q": f"0{alpha_id}"})
    assert padded.json()["total"] == 0

    missing = client.get("/api/admin/products", params={"q": "999999"})
    assert missing.json()["total"] == 0


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


def test_category_uz_and_en_names_are_stored_on_translations(client: TestClient, engine) -> None:
    _seed(engine)
    headers = _auth(client)
    created = client.post(
        "/api/admin/categories",
        json={
            "name_ru": "другие устройства",
            "name_uz": "Boshqa qurilmalar",
            "name_en": "Other devices",
            "is_published": True,
        },
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["name_ru"] == "другие устройства"
    assert created.json()["name_uz"] == "Boshqa qurilmalar"
    assert created.json()["name_en"] == "Other devices"
    category_id = created.json()["id"]
    patched = client.patch(
        f"/api/admin/categories/{category_id}",
        json={
            "name_ru": "другие устройства",
            "name_uz": "Boshqa qurilmalar",
            "name_en": "Other devices",
            "is_published": True,
        },
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["name_ru"] == "другие устройства"
    assert patched.json()["name_uz"] == "Boshqa qurilmalar"
    assert patched.json()["name_en"] == "Other devices"
    slug = created.json()["slug"]
    for locale, name in (
        ("ru", "другие устройства"),
        ("uz", "Boshqa qurilmalar"),
        ("en", "Other devices"),
    ):
        public = client.get(f"/api/public/categories/{slug}", params={"locale": locale})
        assert public.status_code == 200
        assert public.json()["name"] == name
        assert public.json()["translation_fallback"] is False


def test_other_brand_is_created_once_and_assigned_only_when_chosen(client: TestClient, engine) -> None:
    _seed(engine)
    headers = _auth(client)
    hikvision = client.post(
        "/api/admin/brands",
        json={"name_ru": "Hikvision", "name_en": "Hikvision", "is_published": True},
        headers=headers,
    )
    assert hikvision.status_code == 201
    assert hikvision.json()["slug"] == "hikvision"
    other_body = {
        "name_ru": "Другие",
        "name_uz": "Boshqalar",
        "name_en": "Other",
        "is_published": False,
    }
    other = client.post("/api/admin/brands", json=other_body, headers=headers)
    assert other.status_code == 201
    assert other.json()["slug"] == "other"
    assert other.json()["name_ru"] == "Другие"
    assert other.json()["name_uz"] == "Boshqalar"
    assert other.json()["name_en"] == "Other"
    assert other.json()["description_ru"] is None
    assert other.json()["is_published"] is False
    repeat = client.post(
        "/api/admin/brands",
        json={**other_body, "is_published": True, "description_ru": "A manufacturer"},
        headers=headers,
    )
    assert repeat.status_code == 201
    assert repeat.json()["id"] == other.json()["id"]
    assert repeat.json()["is_published"] is False
    assert repeat.json()["description_ru"] is None
    listed = client.get("/api/admin/brands", headers=headers)
    assert listed.status_code == 200
    assert [item["slug"] for item in listed.json()["brands"]].count("other") == 1
    real = client.post(
        "/api/admin/products",
        json=_product("DS-HIK", brand_id=hikvision.json()["id"]),
        headers=headers,
    )
    grouped = client.post(
        "/api/admin/products",
        json=_product("DS-OTHER", brand_id=other.json()["id"]),
        headers=headers,
    )
    bare = client.post("/api/admin/products", json=_product("DS-BARE"), headers=headers)
    assert real.status_code == 201
    assert grouped.status_code == 201
    assert bare.status_code == 201
    assert real.json()["brand_id"] == hikvision.json()["id"]
    assert grouped.json()["brand_id"] == other.json()["id"]
    assert bare.json()["brand_id"] is None


def test_delete_requires_auth_confirmation_and_preserves_shared_history(client: TestClient, engine) -> None:
    _seed(engine)
    headers = _auth(client)
    category = client.post(
        "/api/admin/categories",
        json={"name_ru": "другие устройства", "is_published": False},
        headers=headers,
    )
    assert category.status_code == 201
    category_id = category.json()["id"]
    removed = client.post("/api/admin/products", json=_product("TEST-DO-NOT-SELL-001"), headers=headers)
    keeper = client.post("/api/admin/products", json=_product("Keeper"), headers=headers)
    flexible = client.post(
        "/api/admin/products",
        json=_product("гибкий переход", category_id=category_id, catalog_status="draft", price={"status": "numeric", "amount": "1.50"}),
        headers=headers,
    )
    assert removed.status_code == keeper.status_code == flexible.status_code == 201
    removed_id = removed.json()["id"]
    keeper_id = keeper.json()["id"]
    flexible_id = flexible.json()["id"]
    assert flexible.json()["category_id"] == category_id
    assert flexible.json()["catalog_status"] == "draft"
    assert flexible.json()["category_locked"] is True

    shared = png_bytes(1)
    exclusive = png_bytes(2)
    for product_id, payload, name in ((removed_id, shared, "shared.png"), (keeper_id, shared, "shared.png"), (removed_id, exclusive, "only.png")):
        uploaded = client.post(
            f"/api/admin/products/{product_id}/images",
            files={"file": (name, payload, "image/png")},
            headers=headers,
        )
        assert uploaded.status_code == 201
    with Session(bind=engine) as db:
        admin = db.scalar(select(AdminUser))
        assert admin is not None
        flexible_row = db.get(Product, flexible_id)
        assert flexible_row is not None
        flexible_row.category_locked = False
        job = ImportJob(created_by=admin.id, status="applied", applied_at=func.now())
        db.add(job)
        db.flush()
        stored = ImportFile(
            job_id=job.id,
            source_code="hikvision",
            original_filename="Hikvision pr.xlsx",
            sha256="a" * 64,
            stored_object_key="private-uploads/test",
        )
        db.add(stored)
        db.flush()
        db.add(
            ImportRow(
                import_file_id=stored.id,
                worksheet_name="другие устройства",
                source_row=75,
                classification="product",
                action="unchanged",
                raw_cells={"C": "гибкий переход"},
                proposal={},
                matched_product_id=removed_id,
                applied=True,
            )
        )
        shared_key = db.scalar(select(ProductImage.object_key).where(ProductImage.product_id == keeper_id))
        exclusive_key = db.scalar(
            select(ProductImage.object_key).where(ProductImage.product_id == removed_id, ProductImage.object_key != shared_key)
        )
        assert shared_key is not None and exclusive_key is not None
        shared_image = db.scalar(select(ProductImage).where(ProductImage.object_key == shared_key))
        assert shared_image is not None
        db.add(
            ImportAsset(
                import_file_id=stored.id,
                object_key=shared_key,
                sha256=shared_image.sha256.strip(),
                mime_type="image/png",
                worksheet="другие устройства",
                link_status="linked_high",
                proposed_product_id=removed_id,
            )
        )
        db.add(
            ProductSourceRecord(
                product_id=removed_id,
                source_code="hikvision",
                source_workbook="Hikvision pr.xlsx",
                source_worksheet="другие устройства",
                source_row=75,
                source_model_raw="TEST-DO-NOT-SELL-001",
                source_price_kind="numeric",
                source_price_amount=1,
                match_key="hikvision|other|test-delete",
                first_job_id=job.id,
                last_job_id=job.id,
            )
        )
        db.commit()
        job_id = job.id

    confirmed = client.patch(
        f"/api/admin/products/{flexible_id}",
        json=_product(
            "гибкий переход",
            category_id=category_id,
            catalog_status="draft",
            price={"status": "numeric", "amount": "1.50"},
            lock_category=True,
        ),
        headers=headers,
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["category_id"] == category_id
    assert confirmed.json()["category_locked"] is True
    assert confirmed.json()["catalog_status"] == "draft"
    assert confirmed.json()["public_price_amount"] == "1.50"

    with TestClient(client.app) as anonymous:
        assert anonymous.post(
            f"/api/admin/products/{removed_id}/delete",
            json={"confirm": True, "model_display": "TEST-DO-NOT-SELL-001"},
        ).status_code == 401
    assert client.post(
        f"/api/admin/products/{removed_id}/delete",
        json={"confirm": True, "model_display": "TEST-DO-NOT-SELL-001"},
        headers={"Origin": ORIGIN},
    ).status_code == 403
    assert client.post(
        f"/api/admin/products/{removed_id}/delete",
        json={"confirm": False, "model_display": "TEST-DO-NOT-SELL-001"},
        headers=headers,
    ).status_code == 422
    assert client.post(
        f"/api/admin/products/{removed_id}/delete",
        json={"confirm": True, "model_display": "something-else"},
        headers=headers,
    ).status_code == 422

    deleted = client.post(
        f"/api/admin/products/{removed_id}/delete",
        json={"confirm": True, "model_display": "TEST-DO-NOT-SELL-001"},
        headers=headers,
    )
    assert deleted.status_code == 204
    assert client.get(f"/api/admin/products/{removed_id}").status_code == 404
    listed = client.get("/api/admin/products", params={"q": "TEST-DO-NOT-SELL-001"})
    assert listed.json()["total"] == 0
    assert client.get(f"/api/admin/products/{keeper_id}").status_code == 200

    media_root = Path(client.app.state.settings.media_root)
    with Session(bind=engine) as db:
        assert db.get(Product, removed_id) is None
        assert db.get(Product, keeper_id) is not None
        assert db.get(Product, flexible_id) is not None
        assert db.scalar(select(func.count()).select_from(ProductSourceRecord).where(ProductSourceRecord.product_id == removed_id)) == 0
        row = db.scalar(select(ImportRow).where(ImportRow.source_row == 75))
        assert row is not None
        assert row.matched_product_id is None
        assert db.get(ImportJob, job_id) is not None
        asset = db.scalar(select(ImportAsset))
        assert asset is not None
        assert asset.proposed_product_id is None
        assert asset.object_key == shared_key
        audit = db.scalar(select(AdminAuditLog).where(AdminAuditLog.action == "product_deleted"))
        assert audit is not None
        assert audit.entity_id == removed_id
        assert audit.detail == {"model_display": "TEST-DO-NOT-SELL-001", "catalog_status": "draft"}
        keeper_image = db.scalar(select(ProductImage).where(ProductImage.product_id == keeper_id))
        assert keeper_image is not None
        assert keeper_image.object_key == shared_key
    assert (media_root / shared_key).is_file()
    assert not (media_root / exclusive_key).exists()


def test_draft_model_correction_updates_slug_and_published_copy(client: TestClient, engine) -> None:
    _seed(engine)
    headers = _auth(client)
    supply = client.post(
        "/api/admin/products",
        json=_product(
            "2V 15A",
            catalog_status="draft",
            price={"status": "numeric", "amount": "5.00"},
            translations={
                "ru": {
                    "localized_name": "2V 15A",
                    "description": "Блок питания, выходное напряжение: 12V, выходной ток: 15A",
                }
            },
        ),
        headers=headers,
    )
    assert supply.status_code == 201
    supply_id = supply.json()["id"]
    assert supply.json()["slug"] == "product-2v-15a"
    published = client.patch(
        f"/api/admin/products/{supply_id}",
        json=_product(
            "12V 15A",
            catalog_status="published",
            price={"status": "numeric", "amount": "5.00"},
            translations={
                "ru": {
                    "localized_name": "12V 15A",
                    "description": "Блок питания, рабочее напряжение: 110V/220V± 15%, выходное напряжение: 12V, выходной ток: 15A",
                },
                "uz": {
                    "description": "Quvvat bloki, ish kuchlanishi: 110V/220V ± 15%, chiqish kuchlanishi: 12V, chiqish toki: 15A.",
                },
                "en": {
                    "description": "Power supply, operating voltage: 110V/220V ± 15%, output voltage: 12V, output current: 15A.",
                },
            },
        ),
        headers=headers,
    )
    assert published.status_code == 200
    body = published.json()
    assert body["model_display"] == "12V 15A"
    assert body["slug"] == "product-12v-15a"
    assert body["catalog_status"] == "published"
    assert body["public_price_amount"] == "5.00"
    assert body["price_locked"] is True
    assert "2V 15A" not in body["translations"]["ru"]["description"]
    assert "12V" in body["translations"]["ru"]["description"]
    assert "15A" in body["translations"]["ru"]["description"]

    camera = client.post(
        "/api/admin/products",
        json=_product("DS-2SE4C425MWG-E 14", catalog_status="published", price={"status": "numeric", "amount": "360.00"}),
        headers=headers,
    )
    assert camera.status_code == 201
    original_slug = camera.json()["slug"]
    renamed = client.patch(
        f"/api/admin/products/{camera.json()['id']}",
        json=_product(
            "DS-2SE4C425MWG-E 14X",
            catalog_status="published",
            price={"status": "numeric", "amount": "360.00"},
            translations={
                "ru": {"localized_name": "DS-2SE4C425MWG-E 14X", "description": "15-кратным оптическим зумом и 16-кратным цифровым зумом"},
                "en": {"description": "15x optical zoom and 16x digital zoom"},
            },
        ),
        headers=headers,
    )
    assert renamed.status_code == 200
    assert renamed.json()["slug"] == original_slug
    assert "25x" not in renamed.json()["translations"]["en"]["description"]
    assert "25" not in renamed.json()["translations"]["ru"]["description"]


def test_unchanged_specifications_keep_their_rows(client: TestClient, engine) -> None:
    _seed(engine)
    headers = _auth(client)
    spec = {
        "sort_order": 0,
        "name_ru": "Питание",
        "value_ru": "12 В",
        "name_uz": "Quvvat",
        "value_uz": "12 V",
        "name_en": "Power",
        "value_en": "12 V",
    }
    created = client.post("/api/admin/products", json=_product(specifications=[spec]), headers=headers)
    assert created.status_code == 201
    product_id = created.json()["id"]
    spec_id = created.json()["specifications"][0]["id"]
    same = client.patch(f"/api/admin/products/{product_id}", json=_product(specifications=[spec]), headers=headers)
    assert same.status_code == 200
    assert same.json()["specifications"][0]["id"] == spec_id
    assert same.json()["specifications"][0]["translations"]["uz"]["value"] == "12 V"
    with Session(bind=engine) as db:
        audit = db.scalar(select(AdminAuditLog).order_by(AdminAuditLog.id.desc()))
        assert audit is not None
        assert "specifications" not in (audit.detail or {}).get("changes", [])
    changed = dict(spec)
    changed["value_ru"] = "24 В"
    updated = client.patch(
        f"/api/admin/products/{product_id}", json=_product(specifications=[changed]), headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["specifications"][0]["id"] != spec_id
    assert updated.json()["specifications"][0]["translations"]["ru"]["value"] == "24 В"
    assert updated.json()["specifications"][0]["translations"]["en"]["value"] == "12 V"
