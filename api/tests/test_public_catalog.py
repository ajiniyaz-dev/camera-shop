import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.config import Settings, get_settings
from app.main import create_app
from app.models import (
    AdminUser,
    Brand,
    BrandTranslation,
    BusinessProfile,
    Category,
    CategoryTranslation,
    Product,
    ProductImage,
    ProductSpecification,
    ProductSpecificationTranslation,
    ProductTranslation,
)

API_ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct-horse-1"
ORIGIN = "http://testserver"
ADMIN_URLS = [
    os.environ.get("PHASE2A_ADMIN_URL"),
    "postgresql+psycopg://catalog:change-me@127.0.0.1:5433/postgres",
    "postgresql+psycopg://catalog:catalog@127.0.0.1:5432/postgres",
]
PRIVATE_KEYS = {
    "source",
    "source_code",
    "source_workbook",
    "source_worksheet",
    "source_row",
    "source_price_kind",
    "source_price_header",
    "internal_note",
    "match_key",
    "sha256",
    "object_key",
    "price_locked",
    "option_locked",
    "brand_locked",
    "category_locked",
    "model_locked",
    "description_locked",
    "seo_title",
    "seo_description",
    "origin",
    "association_status",
    "anchor_row",
    "password",
    "password_hash",
    "stock_status",
    "catalog_status",
    "deleted_at",
    "quantity",
}


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
    pytest.fail("PostgreSQL is not reachable for the disposable Phase 6 database")


def _alembic(database_url: str) -> Config:
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    return config


@pytest.fixture(scope="module")
def database_url():
    admin_url, admin_engine = _admin_engine()
    name = "catalog_phase6_test"
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


def _product(db: Session, **values: object) -> Product:
    product = Product(
        product_kind="product",
        model_raw=str(values.get("model_display", "Model")),
        model_normalized=str(values.get("model_display", "Model")).casefold(),
        public_price_status="on_request",
        slug=str(values["slug"]),
        catalog_status="published",
        model_display=str(values.get("model_display", "Model")),
    )
    for key, value in values.items():
        setattr(product, key, value)
    db.add(product)
    db.flush()
    return product


def _translation(product: Product, locale: str, name: str | None, description: str | None = None) -> None:
    product.translations.append(
        ProductTranslation(
            locale=locale,
            localized_name=name,
            description=description,
            origin="manual",
        )
    )


def _seed(engine) -> None:
    db = Session(bind=engine)
    try:
        brand = Brand(slug="hikvision", is_published=True)
        brand.translations.append(BrandTranslation(locale="ru", name="Hikvision"))
        brand.translations.append(BrandTranslation(locale="en", name="Hikvision"))
        quiet = Brand(slug="quiet", is_published=False)
        quiet.translations.append(BrandTranslation(locale="ru", name="Quiet"))
        cameras = Category(slug="cameras", sort_order=1, is_published=True)
        cameras.translations.append(CategoryTranslation(locale="ru", name="Камеры", description="Группа камер"))
        cameras.translations.append(CategoryTranslation(locale="en", name="Cameras"))
        domes = Category(slug="domes", sort_order=1, is_published=True, parent=cameras)
        domes.translations.append(CategoryTranslation(locale="ru", name="Купольные"))
        secret = Category(slug="secret", sort_order=9, is_published=False)
        secret.translations.append(CategoryTranslation(locale="ru", name="Скрытая"))
        db.add_all([brand, quiet, cameras, domes, secret])
        db.flush()
        profile = db.get(BusinessProfile, 1)
        if profile is not None:
            profile.public_name = "HikVision"
            profile.phone = None
            profile.email = None
            profile.address = None
            profile.opening_hours = None
            profile.social_links = None
            profile.logo_object_key = None

        child = _product(
            db,
            slug="child-cam",
            model_display="DS-2CD2143",
            option_label="2.8 mm",
            brand_id=brand.id,
            category_id=domes.id,
            public_price_status="numeric",
            public_price_amount=Decimal("30.00"),
            public_currency="USD",
        )
        _translation(child, "ru", "Купольная", "Описание купола")
        _translation(child, "en", "Dome camera", "Dome description")
        spec = ProductSpecification(product_id=child.id, sort_order=1)
        spec.translations.append(ProductSpecificationTranslation(locale="ru", name="Разрешение", value="4 Мп"))
        db.add(spec)
        db.add_all(
            [
                ProductImage(
                    product_id=child.id,
                    storage_backend="local",
                    object_key="objects/aa/review.png",
                    mime_type="image/png",
                    byte_size=10,
                    sha256="a" * 64,
                    sort_order=0,
                    is_primary=False,
                    association_status="needs_review",
                ),
                ProductImage(
                    product_id=child.id,
                    storage_backend="local",
                    object_key="objects/bb/primary.png",
                    mime_type="image/png",
                    byte_size=20,
                    sha256="b" * 64,
                    width=800,
                    height=600,
                    sort_order=2,
                    is_primary=True,
                    alt_text="Front",
                    association_status="confirmed",
                ),
                ProductImage(
                    product_id=child.id,
                    storage_backend="local",
                    object_key="objects/cc/second.png",
                    mime_type="image/png",
                    byte_size=20,
                    sha256="c" * 64,
                    sort_order=1,
                    is_primary=False,
                    association_status="high",
                ),
                ProductImage(
                    product_id=child.id,
                    storage_backend="local",
                    object_key="objects/dd/reject.png",
                    mime_type="image/png",
                    byte_size=20,
                    sha256="d" * 64,
                    sort_order=3,
                    is_primary=False,
                    association_status="rejected",
                ),
            ]
        )
        parent = _product(
            db,
            slug="parent-cam",
            model_display="DS-2CD2143",
            option_label="4 mm",
            brand_id=brand.id,
            category_id=cameras.id,
            public_price_status="numeric",
            public_price_amount=Decimal("10.00"),
            public_currency="USD",
        )
        _translation(parent, "ru", "Родительская", None)
        _translation(parent, "uz", "Gumbaz", "Gumbaz tavsifi")
        low = _product(
            db,
            slug="priced-low",
            model_display="AAA-LOW",
            public_price_status="numeric",
            public_price_amount=Decimal("10.00"),
            public_currency="USD",
        )
        _translation(low, "ru", "Низкая", None)
        high = _product(
            db,
            slug="priced-high",
            model_display="AAA-HIGH",
            public_price_status="numeric",
            public_price_amount=Decimal("20.50"),
            public_currency="USD",
        )
        _translation(high, "ru", "Высокая", None)
        request = _product(db, slug="request-cam", model_display="DS-2CD-REQ", stock_status="out_of_stock")
        _translation(request, "ru", "По запросу модель", None)
        hidden = _product(
            db,
            slug="hidden-price",
            model_display="DS-HIDDEN",
            public_price_status="hidden",
            public_price_amount=Decimal("5.00"),
        )
        _translation(hidden, "ru", "Скрытая цена", None)
        draft = _product(db, slug="draft-cam", model_display="DS-DRAFT", catalog_status="draft")
        _translation(draft, "ru", "Черновик", None)
        archived = _product(db, slug="archived-cam", model_display="DS-ARCHIVED", catalog_status="archived")
        _translation(archived, "ru", "Архив", None)
        deleted = _product(
            db,
            slug="deleted-cam",
            model_display="DS-DELETED",
            deleted_at=datetime.now(timezone.utc),
        )
        _translation(deleted, "ru", "Удалена", None)
        quiet_product = _product(
            db,
            slug="quiet-cam",
            model_display="DS-QUIET",
            brand_id=quiet.id,
            category_id=secret.id,
        )
        _translation(quiet_product, "ru", "Тихая", None)
        for index in range(3):
            same = _product(db, slug=f"same-{index}", model_display="SAME")
            _translation(same, "ru", "Одинаковая", None)
        db.commit()
    finally:
        db.close()


def _walk(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert key not in PRIVATE_KEYS
            lowered = key.casefold()
            assert "dealer" not in lowered
            assert "audit" not in lowered
            _walk(item)
    elif isinstance(value, list):
        for item in value:
            _walk(item)


def test_public_catalog_lists_only_published_products(client: TestClient, engine) -> None:
    _seed(engine)
    listed = client.get("/api/public/products", params={"locale": "ru", "page_size": 48})
    assert listed.status_code == 200
    assert listed.headers["cache-control"] == "no-store"
    body = listed.json()
    slugs = {item["slug"] for item in body["products"]}
    assert "child-cam" in slugs
    assert "parent-cam" in slugs
    assert "draft-cam" not in slugs
    assert "archived-cam" not in slugs
    assert "deleted-cam" not in slugs
    _walk(body)
    same = [item["slug"] for item in body["products"] if item["model_display"] == "SAME"]
    assert same == ["same-0", "same-1", "same-2"]
    twins = [item for item in body["products"] if item["model_display"] == "DS-2CD2143"]
    assert {item["slug"] for item in twins} == {"child-cam", "parent-cam"}
    assert {item["option_label"] for item in twins} == {"2.8 mm", "4 mm"}


def test_filters_search_sort_and_pagination(client: TestClient, engine) -> None:
    _seed(engine)
    cameras = client.get(
        "/api/public/products",
        params={"locale": "ru", "category": "cameras", "page_size": 48},
    )
    assert cameras.status_code == 200
    assert {item["slug"] for item in cameras.json()["products"]} == {"child-cam", "parent-cam"}
    domes = client.get(
        "/api/public/products",
        params={"locale": "en", "category": "domes", "parent": "cameras", "page_size": 48},
    )
    assert {item["slug"] for item in domes.json()["products"]} == {"child-cam"}
    assert client.get("/api/public/products", params={"locale": "ru", "category": "domes"}).status_code == 404
    brand = client.get("/api/public/products", params={"locale": "ru", "brand": "hikvision", "page_size": 48})
    assert {item["slug"] for item in brand.json()["products"]} == {"child-cam", "parent-cam"}
    assert client.get("/api/public/products", params={"locale": "ru", "brand": "quiet"}).status_code == 404
    found = client.get("/api/public/products", params={"locale": "uz", "q": "Gumbaz"})
    assert [item["slug"] for item in found.json()["products"]] == ["parent-cam"]
    escaped = client.get("/api/public/products", params={"locale": "ru", "q": "%"})
    assert escaped.json()["total"] == 0
    priced = client.get(
        "/api/public/products",
        params={"locale": "ru", "min_price": "15.00", "max_price": "25", "sort": "price_asc"},
    )
    assert [item["slug"] for item in priced.json()["products"]] == ["priced-high"]
    assert priced.json()["products"][0]["price"] == {"status": "numeric", "amount": "20.50", "currency": "USD"}
    ordered = client.get("/api/public/products", params={"locale": "ru", "sort": "price_asc", "page_size": 48})
    order = [item["slug"] for item in ordered.json()["products"]]
    assert order.index("priced-low") < order.index("priced-high") < order.index("request-cam")
    assert order.index("priced-high") < order.index("hidden-price")
    named = client.get("/api/public/products", params={"locale": "ru", "sort": "name", "page_size": 48})
    named_order = [item["slug"] for item in named.json()["products"]]
    assert named_order.index("priced-high") < named_order.index("priced-low")
    descending = client.get("/api/public/products", params={"locale": "ru", "sort": "price_desc", "page_size": 48})
    desc_order = [item["slug"] for item in descending.json()["products"]]
    assert desc_order.index("priced-high") < desc_order.index("priced-low") < desc_order.index("request-cam")
    pages = [
        client.get("/api/public/products", params={"locale": "ru", "q": "SAME", "page_size": 1, "page": page}).json()
        for page in (1, 2, 3)
    ]
    assert [page["products"][0]["slug"] for page in pages] == ["same-0", "same-1", "same-2"]
    assert pages[0]["total"] == 3
    assert client.get("/api/public/products", params={"locale": "ru", "page": 0}).status_code == 422
    assert client.get("/api/public/products", params={"locale": "ru", "page_size": 49}).status_code == 422
    assert client.get("/api/public/products", params={"locale": "ru", "sort": "secret"}).status_code == 422
    assert client.get("/api/public/products", params={"locale": "de"}).status_code == 422
    assert client.get("/api/public/products", params={"locale": "ru", "min_price": "-1"}).status_code == 422
    assert client.get(
        "/api/public/products", params={"locale": "ru", "min_price": "30", "max_price": "1"}
    ).status_code == 422


def test_product_detail_prices_images_and_fallback(client: TestClient, engine) -> None:
    _seed(engine)
    detail = client.get("/api/public/products/child-cam", params={"locale": "uz"})
    assert detail.status_code == 200
    body = detail.json()
    _walk(body)
    assert body["name"] == "Купольная"
    assert body["translation_fallback"] is True
    assert body["description"] == "Описание купола"
    assert body["description_fallback"] is True
    assert body["specifications"] == [
        {"name": "Разрешение", "value": "4 Мп", "translation_fallback": True}
    ]
    assert [image["url"] for image in body["images"]] == [
        "/media/objects/bb/primary.png",
        "/media/objects/cc/second.png",
    ]
    assert body["image"]["url"] == "/media/objects/bb/primary.png"
    assert body["image"]["alt"] == "Front"
    assert body["price"] == {"status": "numeric", "amount": "30.00", "currency": "USD"}
    assert body["out_of_stock"] is False
    assert body["category"]["slug"] == "domes"
    assert body["category"]["parent_slug"] == "cameras"
    assert [item["slug"] for item in body["category"]["breadcrumb"]] == ["cameras", "domes"]
    english = client.get("/api/public/products/child-cam", params={"locale": "en"}).json()
    assert english["name"] == "Dome camera"
    assert english["translation_fallback"] is False
    requested = client.get("/api/public/products/request-cam", params={"locale": "ru"}).json()
    assert requested["price"] == {"status": "on_request", "amount": None, "currency": None}
    assert requested["out_of_stock"] is True
    assert requested["image"] is None
    assert requested["images"] == []
    assert requested["description"] is None
    hidden = client.get("/api/public/products/hidden-price", params={"locale": "ru"}).json()
    assert hidden["price"] == {"status": "hidden", "amount": None, "currency": None}
    quiet = client.get("/api/public/products/quiet-cam", params={"locale": "ru"}).json()
    assert quiet["brand"] is None
    assert quiet["category"] is None
    for slug in ("draft-cam", "archived-cam", "deleted-cam", "missing-cam"):
        assert client.get(f"/api/public/products/{slug}", params={"locale": "ru"}).status_code == 404


def test_categories_brands_and_company_are_public(client: TestClient, engine) -> None:
    _seed(engine)
    tree = client.get("/api/public/categories", params={"locale": "ru"})
    assert tree.status_code == 200
    categories = tree.json()["categories"]
    assert [item["slug"] for item in categories] == ["cameras"]
    assert categories[0]["name"] == "Камеры"
    assert categories[0]["description"] == "Группа камер"
    assert categories[0]["product_count"] == 2
    assert categories[0]["children"][0]["slug"] == "domes"
    assert categories[0]["children"][0]["product_count"] == 1
    assert "secret" not in str(categories)
    nested = client.get("/api/public/categories/cameras/domes", params={"locale": "en"})
    assert nested.status_code == 200
    assert nested.json()["name"] == "Купольные"
    assert nested.json()["translation_fallback"] is True
    assert client.get("/api/public/categories/domes", params={"locale": "ru"}).status_code == 404
    assert client.get("/api/public/categories/secret", params={"locale": "ru"}).status_code == 404
    brand = client.get("/api/public/brands/hikvision", params={"locale": "uz"})
    assert brand.status_code == 200
    assert brand.json()["name"] == "Hikvision"
    assert brand.json()["translation_fallback"] is True
    assert client.get("/api/public/brands/quiet", params={"locale": "ru"}).status_code == 404
    home = client.get("/api/public/home", params={"locale": "ru"})
    assert home.status_code == 200
    assert home.json()["company"] == {"name": "HikVision"}
    assert "draft-cam" not in {item["slug"] for item in home.json()["products"]}
    db = Session(bind=engine)
    try:
        row = db.get(BusinessProfile, 1)
        assert row is not None
        row.phone = "  "
        row.email = "desk@example.com"
        row.logo_object_key = "private-uploads/logo.png"
        row.social_links = [
            {"label": "Site", "url": "javascript:alert(1)"},
            {"label": "Channel", "url": "https://example.com/channel"},
        ]
        db.commit()
    finally:
        db.close()
    company = client.get("/api/public/company", params={"locale": "en"})
    assert company.status_code == 200
    assert company.json() == {
        "name": "HikVision",
        "email": "desk@example.com",
        "social_links": [{"label": "Channel", "url": "https://example.com/channel"}],
    }


def test_public_routes_do_not_weaken_admin_protection(client: TestClient, engine) -> None:
    _seed(engine)
    db = Session(bind=engine)
    try:
        db.add(AdminUser(email="admin@example.com", password_hash=hash_password(PASSWORD), role="admin"))
        db.commit()
    finally:
        db.close()
    assert client.get("/api/public/products", params={"locale": "ru"}).status_code == 200
    assert client.get("/api/admin/dashboard").status_code == 401
    assert client.post(
        "/api/admin/products",
        json={"model_display": "Blocked", "price": {"status": "on_request"}, "translations": {}},
        headers={"Origin": ORIGIN},
    ).status_code == 401
    login = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": PASSWORD},
        headers={"Origin": ORIGIN},
    )
    assert login.status_code == 200
    denied = client.post(
        "/api/admin/products",
        json={"model_display": "Blocked", "price": {"status": "on_request"}, "translations": {}},
        headers={"Origin": ORIGIN},
    )
    assert denied.status_code == 403
