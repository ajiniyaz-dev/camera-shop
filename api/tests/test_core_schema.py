import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
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
CORE_TABLES = {
    "admin_users",
    "brand_translations",
    "brands",
    "business_profile",
    "categories",
    "category_translations",
    "product_images",
    "product_source_records",
    "product_specification_translations",
    "product_specifications",
    "product_translations",
    "products",
}
IMPORT_TABLES = {
    "admin_audit_log",
    "import_assets",
    "import_files",
    "import_jobs",
    "import_rows",
}
DEFERRED_TABLES = {
    "admin_sessions",
    "slug_redirects",
}
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
    pytest.fail("PostgreSQL is not reachable for the disposable Phase 2A database")


def _upgrade(database_url: str) -> None:
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    try:
        command.upgrade(config, "head")
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()


def _recreate(admin_engine, database_name: str, admin_url: str) -> str:
    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    return admin_url.rsplit("/", 1)[0] + "/" + database_name


@pytest.fixture(scope="module")
def schema_engine():
    admin_url, admin_engine = _admin_engine()
    database_url = _recreate(admin_engine, "catalog_phase2a_test", admin_url)
    try:
        _upgrade(database_url)
        engine = create_engine(database_url)
        yield engine
        engine.dispose()
    finally:
        with admin_engine.connect() as connection:
            connection.execute(text('DROP DATABASE IF EXISTS "catalog_phase2a_test" WITH (FORCE)'))
        admin_engine.dispose()


@pytest.fixture
def db(schema_engine):
    connection = schema_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


def _product(session: Session, slug: str, **overrides: object) -> Product:
    values: dict[str, object] = {
        "product_kind": "product",
        "model_raw": "CS-H8c (3MP)",
        "model_display": "CS-H8c (3MP)",
        "model_normalized": "cs-h8c (3mp)",
        "public_price_status": "on_request",
        "slug": slug,
        "catalog_status": "draft",
    }
    values.update(overrides)
    product = Product(**values)
    session.add(product)
    session.flush()
    session.refresh(product)
    return product


def _applied_job(session: Session) -> ImportJob:
    job = session.scalars(select(ImportJob).limit(1)).first()
    if job is not None:
        return job
    admin = AdminUser(email="schema-job@example.com", password_hash="stored-hash", role="admin")
    session.add(admin)
    session.flush()
    job = ImportJob(
        status="applied",
        created_by=admin.id,
        approved_by=admin.id,
        applied_at=datetime.now(timezone.utc),
    )
    session.add(job)
    session.flush()
    return job


def _source(session: Session, product: Product, match_key: str, **overrides: object) -> ProductSourceRecord:
    job = _applied_job(session)
    values: dict[str, object] = {
        "product_id": product.id,
        "source_code": "hikvision",
        "source_workbook": "Hikvision pr.xlsx",
        "source_worksheet": "HDD",
        "source_row": 2,
        "source_model_raw": product.model_raw,
        "source_price_kind": "blank",
        "match_key": match_key,
        "first_job_id": job.id,
        "last_job_id": job.id,
    }
    values.update(overrides)
    record = ProductSourceRecord(**values)
    session.add(record)
    session.flush()
    return record


def _image(session: Session, product: Product, **overrides: object) -> ProductImage:
    values: dict[str, object] = {
        "product_id": product.id,
        "storage_backend": "local",
        "object_key": f"objects/ab/{product.slug}.jpg",
        "mime_type": "image/jpeg",
        "byte_size": 1200,
        "sha256": "a" * 64,
        "sort_order": 0,
        "is_primary": False,
        "association_status": "high",
    }
    values.update(overrides)
    image = ProductImage(**values)
    session.add(image)
    session.flush()
    return image


def test_migration_creates_core_tables_and_company_seed(schema_engine) -> None:
    with schema_engine.connect() as connection:
        names = {
            row[0]
            for row in connection.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
        }
        assert CORE_TABLES <= names
        assert IMPORT_TABLES <= names
        assert DEFERRED_TABLES.isdisjoint(names)
        version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert version == "phase2b_import"
        profile = connection.execute(
            text(
                """
                SELECT id, public_name, legal_name, domain, phone, email, address,
                       opening_hours, social_links, logo_object_key
                FROM business_profile
                """
            )
        ).one()
        price = connection.execute(
            text(
                """
                SELECT data_type, numeric_precision, numeric_scale
                FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'public_price_amount'
                """
            )
        ).one()
        unique_indexes = connection.execute(
            text(
                """
                SELECT indexdef
                FROM pg_indexes
                WHERE tablename = 'products' AND indexdef ILIKE 'CREATE UNIQUE%'
                """
            )
        ).scalars().all()
    assert profile.id == 1
    assert profile.public_name == "HikVision"
    assert profile.legal_name is None
    assert profile.domain is None
    assert profile.phone is None
    assert profile.email is None
    assert profile.address is None
    assert profile.opening_hours is None
    assert profile.social_links is None
    assert profile.logo_object_key is None
    assert price.data_type == "numeric"
    assert price.numeric_precision == 12
    assert price.numeric_scale == 2
    assert all("model_normalized" not in definition for definition in unique_indexes)
    assert all("model_display" not in definition and "model_raw" not in definition for definition in unique_indexes)


def test_migration_round_trip_from_empty_database() -> None:
    admin_url, admin_engine = _admin_engine()
    database_url = _recreate(admin_engine, "catalog_phase2a_roundtrip", admin_url)
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    try:
        command.upgrade(config, "head")
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        engine = create_engine(database_url)
        with engine.connect() as connection:
            count = connection.execute(text("SELECT count(*) FROM business_profile")).scalar_one()
            version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        engine.dispose()
        assert count == 1
        assert version == "phase2b_import"
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()
        with admin_engine.connect() as connection:
            connection.execute(text('DROP DATABASE IF EXISTS "catalog_phase2a_roundtrip" WITH (FORCE)'))
        admin_engine.dispose()


def test_repeated_model_names_are_separate_products(db: Session) -> None:
    first = _product(db, "ezviz-cs-h8c-3mp-r35")
    second = _product(db, "ezviz-cs-h8c-3mp-r38")
    assert first.id != second.id
    assert first.model_normalized == second.model_normalized


def test_multiple_images_and_one_primary(db: Session) -> None:
    product = _product(db, "camera-with-photos")
    primary = _image(db, product, is_primary=True, sha256="b" * 64, sort_order=0)
    secondary = _image(
        db,
        product,
        object_key="objects/ab/extra.jpg",
        sha256="c" * 64,
        sort_order=1,
        is_primary=False,
    )
    _image(
        db,
        product,
        object_key="objects/ab/rejected.jpg",
        sha256="d" * 64,
        sort_order=2,
        is_primary=True,
        association_status="rejected",
    )
    assert {primary.id, secondary.id} <= {image.id for image in product.images}
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            _image(
                db,
                product,
                object_key="objects/ab/second-primary.jpg",
                sha256="e" * 64,
                sort_order=3,
                is_primary=True,
                association_status="confirmed",
            )


def test_decimal_price_precision(db: Session) -> None:
    product = _product(
        db,
        "ezviz-cs-dp2c",
        public_price_status="numeric",
        public_price_amount=Decimal("92.5"),
        public_currency="USD",
    )
    db.refresh(product)
    assert product.public_price_amount == Decimal("92.50")
    assert type(product.public_price_amount) is Decimal
    accessory = _product(
        db,
        "accessory-unit",
        model_raw="unit",
        model_display="unit",
        model_normalized="unit",
        public_price_status="numeric",
        public_price_amount=Decimal("0.14"),
        public_currency="USD",
    )
    db.refresh(accessory)
    assert accessory.public_price_amount == Decimal("0.14")


def test_blank_source_price_stays_distinct_from_explicit_request(db: Session) -> None:
    blank_product = _product(db, "hdd-blank-price")
    explicit_product = _product(db, "project-on-request", model_normalized="ds-1005ki")
    blank = _source(db, blank_product, "hikvision|HDD|blank", source_price_kind="blank")
    explicit = _source(
        db,
        explicit_product,
        "hikvision|project|request",
        source_worksheet="Проектное оборудование",
        source_price_kind="explicit_on_request",
        source_price_raw=" По запросу ",
        source_price_header="Цена",
    )
    assert blank_product.public_price_status == "on_request"
    assert explicit_product.public_price_status == "on_request"
    assert blank_product.public_price_amount is None
    assert explicit_product.public_price_amount is None
    assert blank.source_price_kind == "blank"
    assert explicit.source_price_kind == "explicit_on_request"
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            _source(
                db,
                _product(db, "blank-with-zero"),
                "hikvision|HDD|zero",
                source_price_kind="blank",
                source_price_amount=Decimal("0.00"),
            )


def test_stock_status_is_independent_of_price(db: Session) -> None:
    priced = _product(
        db,
        "priced-out-of-stock",
        public_price_status="numeric",
        public_price_amount=Decimal("115.00"),
        public_currency="USD",
        stock_status="out_of_stock",
    )
    requested = _product(db, "request-still-in-stock")
    db.refresh(requested)
    assert priced.stock_status == "out_of_stock"
    assert priced.public_price_status == "numeric"
    assert requested.stock_status == "in_stock"
    assert requested.public_price_status == "on_request"
    priced.stock_status = "in_stock"
    db.flush()
    assert priced.public_price_amount == Decimal("115.00")


def test_brand_delete_is_restricted_and_translations_cascade(db: Session) -> None:
    brand = Brand(slug="ezviz", is_published=True)
    brand.translations.append(BrandTranslation(locale="ru", name="EZVIZ"))
    db.add(brand)
    db.flush()
    product = _product(db, "branded-camera", brand_id=brand.id)
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.delete(brand)
            db.flush()
    db.delete(product)
    db.flush()
    db.delete(brand)
    db.flush()
    assert db.get(BrandTranslation, (brand.id, "ru")) is None


def test_category_children_and_locale_copy(db: Session) -> None:
    parent = Category(slug="hilook", sort_order=0, is_published=True, source_code="hikvision")
    child = Category(slug="nvr", sort_order=1, is_published=True, parent=parent)
    child.translations.append(CategoryTranslation(locale="ru", name="NVR"))
    db.add(parent)
    db.flush()
    assert child.parent_id == parent.id
    product = _product(db, "hilook-nvr", category_id=child.id)
    product.translations.append(
        ProductTranslation(locale="ru", description="Описание", origin="source")
    )
    specification = ProductSpecification(sort_order=0, product_id=product.id)
    db.add(specification)
    db.flush()
    db.add(
        ProductSpecificationTranslation(
            specification_id=specification.id,
            locale="ru",
            name="Разрешение",
            value="4 Мп",
        )
    )
    db.flush()
    assert product.category.slug == "nvr"
    assert product.specifications[0].translations[0].value == "4 Мп"
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.delete(child)
            db.flush()


def test_admin_user_role_and_email_constraints(db: Session) -> None:
    db.add(AdminUser(email="staff@example.com", password_hash="stored-hash", role="admin"))
    db.flush()
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(AdminUser(email="staff@example.com", password_hash="other-hash", role="admin"))
            db.flush()
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(AdminUser(email="other@example.com", password_hash="stored-hash", role="editor"))
            db.flush()


def test_second_company_profile_row_is_rejected(db: Session) -> None:
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(BusinessProfile(id=2, public_name="HikVision"))
            db.flush()
