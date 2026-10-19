import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
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
    ImportJob,
    Product,
    ProductImage,
    ProductSourceRecord,
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
    pytest.fail("PostgreSQL is not reachable for the disposable Phase 7 database")


def _alembic(database_url: str) -> Config:
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    return config


@pytest.fixture(scope="module")
def database_url():
    admin_url, admin_engine = _admin_engine()
    name = "catalog_phase7_test"
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


def _source(
    db: Session,
    product: Product,
    *,
    source_code: str,
    job_id: int,
    worksheet: str = "IP камеры",
    row: int = 2,
) -> None:
    workbook = "Hikvision pr.xlsx" if source_code == "hikvision" else "Ezviz pr.xlsx"
    db.add(
        ProductSourceRecord(
            product_id=product.id,
            source_code=source_code,
            source_workbook=workbook,
            source_worksheet=worksheet,
            source_row=row,
            source_model_raw=product.model_raw,
            source_price_kind="numeric" if product.public_price_status == "numeric" else "blank",
            source_price_amount=product.public_price_amount if product.public_price_status == "numeric" else None,
            match_key=f"{source_code}|{worksheet}|{product.slug}|{row}",
            first_job_id=job_id,
            last_job_id=job_id,
        )
    )


def _seed(engine) -> None:
    db = Session(bind=engine)
    try:
        admin = AdminUser(email="public-seed@example.com", password_hash=hash_password(PASSWORD), role="admin")
        db.add(admin)
        db.flush()
        job = ImportJob(
            status="applied",
            created_by=admin.id,
            approved_by=admin.id,
            applied_at=datetime.now(timezone.utc),
        )
        db.add(job)
        db.flush()
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
        orphan = _product(
            db,
            slug="orphan-cam",
            model_display="ADMIN-ONLY",
            public_price_status="numeric",
            public_price_amount=Decimal("40.00"),
            public_currency="USD",
        )
        _translation(orphan, "ru", "Без источника", None)
        _source(db, child, source_code="hikvision", job_id=job.id, worksheet="Hilook", row=4)
        _source(db, parent, source_code="hikvision", job_id=job.id, row=5)
        _source(db, low, source_code="hikvision", job_id=job.id, row=6)
        _source(db, high, source_code="ezviz", job_id=job.id, worksheet="Ezviz", row=7)
        _source(db, request, source_code="hikvision", job_id=job.id, row=8)
        _source(db, hidden, source_code="hikvision", job_id=job.id, row=9)
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
    # Filters use displayed soʻm. priced-high is EZVIZ 20.50 → 221400; priced-low is Hikvision 10 → 96000.
    priced = client.get(
        "/api/public/products",
        params={"locale": "ru", "min_price": "200000", "max_price": "230000", "sort": "price_asc"},
    )
    assert [item["slug"] for item in priced.json()["products"]] == ["priced-high"]
    assert priced.json()["products"][0]["price"] == {"status": "numeric", "amount": "221400", "currency": "UZS"}
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
    assert client.get("/api/public/products", params={"locale": "ru", "min_price": "15.5"}).status_code == 422
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
    assert body["product_kind"] == "product"
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
    # Hilook sheet still uses the Hikvision workbook factor: 30 * 9600 = 288000.
    assert body["price"] == {"status": "numeric", "amount": "288000", "currency": "UZS"}
    assert body["out_of_stock"] is False
    assert body["category"]["slug"] == "domes"
    assert body["category"]["parent_slug"] == "cameras"
    assert [item["slug"] for item in body["category"]["breadcrumb"]] == ["cameras", "domes"]
    english = client.get("/api/public/products/child-cam", params={"locale": "en"}).json()
    assert english["name"] == "Dome camera"
    assert english["translation_fallback"] is False
    assert english["price"] == {"status": "numeric", "amount": "288000", "currency": "UZS"}
    assert english["image"]["alt"] == "Front"
    requested = client.get("/api/public/products/request-cam", params={"locale": "ru"}).json()
    assert requested["price"] == {"status": "on_request", "amount": None, "currency": None}
    assert requested["out_of_stock"] is True
    assert requested["image"] is None
    assert requested["images"] == []
    assert requested["description"] is None
    hidden = client.get("/api/public/products/hidden-price", params={"locale": "ru"}).json()
    assert hidden["price"] == {"status": "hidden", "amount": None, "currency": None}
    orphan = client.get("/api/public/products/orphan-cam", params={"locale": "ru"}).json()
    assert orphan["price"] == {"status": "unavailable", "amount": None, "currency": None}
    quiet = client.get("/api/public/products/quiet-cam", params={"locale": "ru"}).json()
    assert quiet["brand"] is None
    assert quiet["category"] is None
    for slug in ("draft-cam", "archived-cam", "deleted-cam", "missing-cam"):
        assert client.get(f"/api/public/products/{slug}", params={"locale": "ru"}).status_code == 404
    with Session(bind=engine) as db:
        stored = db.scalar(select(Product).where(Product.slug == "child-cam"))
        assert stored is not None
        assert stored.public_price_amount == Decimal("30.00")
        assert stored.public_currency == "USD"


def test_public_image_alt_prefers_localized_name_over_cyrillic_stored(
    client: TestClient, engine
) -> None:
    from app.public.router import _image_alt

    assert _image_alt(None, "Flexible transition") == "Flexible transition"
    assert _image_alt("Front", "Flexible transition") == "Front"
    assert _image_alt("гибкий переход", "Flexible transition") == "Flexible transition"
    assert _image_alt("гибкий переход", "гибкий переход") == "гибкий переход"
    assert _image_alt("гибкий переход", "Купольная") == "гибкий переход"

    _seed(engine)
    with Session(bind=engine) as db:
        product = db.scalar(select(Product).where(Product.slug == "child-cam"))
        assert product is not None
        primary = db.scalar(
            select(ProductImage).where(
                ProductImage.product_id == product.id,
                ProductImage.is_primary.is_(True),
            )
        )
        assert primary is not None
        primary.alt_text = "гибкий переход"
        db.commit()

    english = client.get("/api/public/products/child-cam", params={"locale": "en"}).json()
    assert english["name"] == "Dome camera"
    assert english["image"]["alt"] == "Dome camera"
    assert english["images"][0]["alt"] == "Dome camera"

    russian = client.get("/api/public/products/child-cam", params={"locale": "ru"}).json()
    assert russian["name"] == "Купольная"
    assert russian["image"]["alt"] == "гибкий переход"


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


def test_category_names_resolve_for_ru_uz_and_en(client: TestClient, engine) -> None:
    """Category display names come from category_translations; missing locales fall back to Russian."""
    _seed(engine)
    with Session(bind=engine) as db:
        other = Category(slug="drugie-ustroystva", sort_order=2, is_published=True)
        other.translations.extend(
            [
                CategoryTranslation(locale="ru", name="другие устройства"),
                CategoryTranslation(locale="uz", name="Boshqa qurilmalar"),
                CategoryTranslation(locale="en", name="Other devices"),
            ]
        )
        incomplete = Category(slug="incomplete-other", sort_order=3, is_published=True)
        incomplete.translations.append(CategoryTranslation(locale="ru", name="только русский"))
        db.add_all([other, incomplete])
        db.commit()

    expected = {
        "ru": ("другие устройства", False),
        "uz": ("Boshqa qurilmalar", False),
        "en": ("Other devices", False),
    }
    for locale, (name, fallback) in expected.items():
        tree = client.get("/api/public/categories", params={"locale": locale})
        assert tree.status_code == 200
        by_slug = {item["slug"]: item for item in tree.json()["categories"]}
        assert by_slug["drugie-ustroystva"]["name"] == name
        assert by_slug["drugie-ustroystva"]["translation_fallback"] is fallback

        detail = client.get("/api/public/categories/drugie-ustroystva", params={"locale": locale})
        assert detail.status_code == 200
        body = detail.json()
        assert body["name"] == name
        assert body["translation_fallback"] is fallback
        assert body["breadcrumb"][-1]["name"] == name

    missing = client.get("/api/public/categories/incomplete-other", params={"locale": "uz"})
    assert missing.status_code == 200
    assert missing.json()["name"] == "только русский"
    assert missing.json()["translation_fallback"] is True


def test_product_title_resolves_for_ru_uz_and_en_without_fallback(client: TestClient, engine) -> None:
    """Localized product titles come from product_translations.localized_name for each locale."""
    _seed(engine)
    with Session(bind=engine) as db:
        product = _product(
            db,
            slug="product-gibkiy-perekhod",
            model_display="гибкий переход",
            catalog_status="published",
            public_price_status="numeric",
            public_price_amount=Decimal("1.50"),
            public_currency="USD",
        )
        _translation(
            product,
            "ru",
            "гибкий переход",
            "Гибкий переход — элемент для переходного соединения компонентов оборудования.",
        )
        _translation(
            product,
            "uz",
            "Egiluvchan o\u2018tish",
            "Egiluvchan o\u2018tish elementi uskunaning qismlarini ulash uchun mo\u2018ljallangan.",
        )
        _translation(
            product,
            "en",
            "Flexible transition",
            "A flexible transition component is used to connect equipment components.",
        )
        db.commit()

    expected = {
        "ru": "гибкий переход",
        "uz": "Egiluvchan o\u2018tish",
        "en": "Flexible transition",
    }
    for locale, name in expected.items():
        detail = client.get("/api/public/products/product-gibkiy-perekhod", params={"locale": locale})
        assert detail.status_code == 200
        body = detail.json()
        assert body["name"] == name
        assert body["translation_fallback"] is False
        assert body["model_display"] == "гибкий переход"

        listing = client.get(
            "/api/public/products",
            params={"locale": locale, "q": name, "page_size": 48},
        )
        assert listing.status_code == 200
        card = next(item for item in listing.json()["products"] if item["slug"] == "product-gibkiy-perekhod")
        assert card["name"] == name
        assert card["translation_fallback"] is False


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


def test_sitemap_lists_published_pages_only(client: TestClient, engine) -> None:
    _seed(engine)
    db = Session(bind=engine)
    try:
        product = db.scalar(select(Product).where(Product.slug == "child-cam"))
        assert product is not None
        for item in product.translations:
            if item.locale == "ru":
                item.seo_title = "Купольная SEO"
                item.seo_description = "Описание для поиска"
        category = db.scalar(select(Category).where(Category.slug == "cameras"))
        assert category is not None
        for item in category.translations:
            if item.locale == "ru":
                item.seo_title = "Камеры SEO"
        db.commit()
    finally:
        db.close()
    response = client.get("/api/public/sitemap")
    assert response.status_code == 200
    entries = response.json()["entries"]
    _walk(entries)
    paths = [item["path"] for item in entries]
    assert len(paths) == len(set(paths))
    for locale in ("ru", "uz", "en"):
        assert f"/{locale}" in paths
        assert f"/{locale}/catalog" in paths
        assert f"/{locale}/categories" in paths
        assert f"/{locale}/contact" in paths
        assert f"/{locale}/categories/cameras" in paths
        assert f"/{locale}/categories/cameras/domes" in paths
        assert f"/{locale}/brands/hikvision" in paths
        assert f"/{locale}/products/child-cam" in paths
        assert f"/{locale}/products/request-cam" in paths
        assert f"/{locale}/products/quiet-cam" in paths
    joined = "\n".join(paths)
    for blocked in ("draft-cam", "archived-cam", "deleted-cam", "/categories/secret", "/brands/quiet"):
        assert blocked not in joined
    assert not any("/search" in path or path.endswith("/products") for path in paths)
    child = next(item for item in entries if item["path"] == "/en/products/child-cam")
    assert child["alternates"]["ru"] == "/ru/products/child-cam"
    assert child["alternates"]["uz"] == "/uz/products/child-cam"
    assert child["alternates"]["en"] == "/en/products/child-cam"
    assert child["alternates"]["x-default"] == "/ru/products/child-cam"
    assert child["last_modified"]
    home = next(item for item in entries if item["path"] == "/ru")
    assert home["last_modified"] is None
    english = client.get("/api/public/products/child-cam", params={"locale": "en"})
    assert english.status_code == 200
    assert english.json()["seo_title"] is None
    assert english.json()["seo_description"] is None
    russian = client.get("/api/public/products/child-cam", params={"locale": "ru"})
    assert russian.json()["seo_title"] == "Купольная SEO"
    assert russian.json()["seo_description"] == "Описание для поиска"
    assert "offers" not in russian.json()
    request = client.get("/api/public/products/request-cam", params={"locale": "ru"})
    assert request.json()["price"] == {"status": "on_request", "amount": None, "currency": None}
    hidden = client.get("/api/public/products/hidden-price", params={"locale": "ru"})
    assert hidden.json()["price"]["amount"] is None
    cameras = client.get("/api/public/categories/cameras", params={"locale": "en"})
    assert cameras.json()["seo_title"] is None
    assert client.get("/api/public/categories/cameras", params={"locale": "ru"}).json()["seo_title"] == "Камеры SEO"


def test_other_brand_is_public_only_with_a_published_product(client: TestClient, engine) -> None:
    _seed(engine)
    db = Session(bind=engine)
    try:
        other = Brand(slug="other", is_published=True)
        other.translations.extend(
            [
                BrandTranslation(locale="ru", name="Другие"),
                BrandTranslation(locale="uz", name="Boshqalar"),
                BrandTranslation(locale="en", name="Other"),
            ]
        )
        vacant = Brand(slug="drugie", is_published=True)
        vacant.translations.append(BrandTranslation(locale="ru", name="Другие"))
        spare = Brand(slug="spare", is_published=True)
        spare.translations.append(BrandTranslation(locale="en", name="Spare"))
        db.add_all([other, vacant, spare])
        db.flush()
        assigned = _product(
            db,
            slug="grouped-cam",
            model_display="BNC-1",
            brand_id=other.id,
            catalog_status="published",
        )
        _translation(assigned, "ru", "BNC-1", "Разъём")
        _translation(assigned, "en", None, "Connector")
        bare = _product(db, slug="unbranded-cam", model_display="BNC-2", catalog_status="published")
        _translation(bare, "en", None, "Loose connector")
        draft = _product(
            db,
            slug="grouped-draft",
            model_display="BNC-3",
            brand_id=vacant.id,
            catalog_status="draft",
        )
        _translation(draft, "ru", None, "Черновик")
        db.commit()
    finally:
        db.close()

    listing = client.get("/api/public/products", params={"locale": "en"})
    assert listing.status_code == 200
    names = {item["slug"]: item["name"] for item in listing.json()["brands"]}
    assert names["hikvision"] == "Hikvision"
    assert names["other"] == "Other"
    assert "spare" not in names
    assert "drugie" not in names
    assert "quiet" not in names
    filtered = client.get("/api/public/products", params={"locale": "en", "brand": "other"})
    assert filtered.status_code == 200
    assert [item["slug"] for item in filtered.json()["products"]] == ["grouped-cam"]
    assert filtered.json()["products"][0]["brand"] == {
        "slug": "other",
        "name": "Other",
        "description": None,
        "translation_fallback": False,
        "description_fallback": False,
    }
    hikvision = client.get("/api/public/products", params={"locale": "ru", "brand": "hikvision"})
    hikvision_slugs = {item["slug"] for item in hikvision.json()["products"]}
    assert "child-cam" in hikvision_slugs
    assert "grouped-cam" not in hikvision_slugs
    assert client.get("/api/public/products", params={"locale": "en", "brand": "drugie"}).status_code == 404
    assert client.get("/api/public/products", params={"locale": "en", "brand": "spare"}).status_code == 404
    detail = client.get("/api/public/brands/other", params={"locale": "en"})
    assert detail.status_code == 200
    assert detail.json()["name"] == "Other"
    assert detail.json()["description"] is None
    assert detail.json()["seo_title"] is None
    assert detail.json()["seo_description"] is None
    assert client.get("/api/public/brands/other", params={"locale": "ru"}).json()["name"] == "Другие"
    assert client.get("/api/public/brands/other", params={"locale": "uz"}).json()["name"] == "Boshqalar"
    assert client.get("/api/public/brands/drugie", params={"locale": "ru"}).status_code == 404
    assert client.get("/api/public/brands/spare", params={"locale": "en"}).status_code == 404
    model_title = client.get("/api/public/products/grouped-cam", params={"locale": "uz"}).json()
    assert model_title["name"] == "BNC-1"
    assert model_title["translation_fallback"] is False
    grouped = client.get("/api/public/products/grouped-cam", params={"locale": "en"}).json()
    assert grouped["brand"]["slug"] == "other"
    assert grouped["description"] == "Connector"
    bare_body = client.get("/api/public/products/unbranded-cam", params={"locale": "en"}).json()
    assert bare_body["brand"] is None
    real = client.get("/api/public/products/child-cam", params={"locale": "en"}).json()
    assert real["brand"]["slug"] == "hikvision"
    paths = [item["path"] for item in client.get("/api/public/sitemap").json()["entries"]]
    assert "/en/brands/other" in paths
    assert "/en/brands/spare" not in paths
    assert "/en/brands/hikvision" in paths
    assert not any(path.endswith("/brands/drugie") for path in paths)
