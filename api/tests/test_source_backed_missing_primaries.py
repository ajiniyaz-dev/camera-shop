"""Source-backed primary backfill for six imageless products (disposable DB only)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.orm import Session, selectinload

from app.auth.passwords import hash_password
from app.config import Settings, get_settings
from app.data.source_backed_missing_primaries import (
    EXPECTED_PRODUCT_IDS,
    SOURCE_BACKED_MISSING_PRIMARIES,
    apply_source_backed_missing_primaries,
    revert_source_backed_missing_primaries,
)
from app.main import create_app
from app.models import (
    AdminUser,
    Brand,
    BrandTranslation,
    Category,
    CategoryTranslation,
    ImportAsset,
    ImportFile,
    ImportJob,
    Product,
    ProductImage,
    ProductSourceRecord,
    ProductTranslation,
)
from tests.import_builders import png_bytes

API_ROOT = Path(__file__).resolve().parents[1]
ADMIN_URLS = [
    os.environ.get("PHASE2A_ADMIN_URL"),
    "postgresql+psycopg://catalog:change-me@127.0.0.1:5433/postgres",
    "postgresql+psycopg://catalog:catalog@127.0.0.1:5432/postgres",
]


def test_specs_cover_exactly_the_six_verified_products() -> None:
    assert set(EXPECTED_PRODUCT_IDS.values()) == {37, 110, 111, 184, 200, 383}
    assert len(SOURCE_BACKED_MISSING_PRIMARIES) == 6
    assert (
        SOURCE_BACKED_MISSING_PRIMARIES["hilook-ds-kis202t"]["sha256"]
        == SOURCE_BACKED_MISSING_PRIMARIES["hilook-vdp-k203"]["sha256"]
    )


def _connect(url: str):
    engine = create_engine(url, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 3})
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        engine.dispose()
        return None
    return engine


@pytest.fixture(scope="module")
def primaries_engine(tmp_path_factory):
    admin_engine = None
    admin_url = None
    for url in ADMIN_URLS:
        if not url:
            continue
        admin_engine = _connect(url)
        if admin_engine is not None:
            admin_url = url
            break
    if admin_engine is None or admin_url is None:
        pytest.skip("PostgreSQL is not reachable for disposable missing-primaries tests")

    name = "catalog_missing_primaries_test"
    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    database_url = admin_url.rsplit("/", 1)[0] + "/" + name
    media_root = tmp_path_factory.mktemp("media-primaries")
    previous = os.environ.get("DATABASE_URL")
    previous_media = os.environ.get("MEDIA_ROOT")
    os.environ["DATABASE_URL"] = database_url
    os.environ["MEDIA_ROOT"] = str(media_root)
    get_settings.cache_clear()
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    try:
        command.upgrade(config, "head")
        engine = create_engine(database_url)
        yield engine, Path(media_root), database_url
        engine.dispose()
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        if previous_media is None:
            os.environ.pop("MEDIA_ROOT", None)
        else:
            os.environ["MEDIA_ROOT"] = previous_media
        get_settings.cache_clear()
        with admin_engine.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin_engine.dispose()


def _ensure_seeded(
    db: Session,
    media_root: Path,
    *,
    slug: str,
) -> Product:
    existing = db.scalar(select(Product).where(Product.slug == slug))
    if existing is not None:
        return existing

    spec = SOURCE_BACKED_MISSING_PRIMARIES[slug]
    worksheet = str(spec["source_worksheet"])
    row = int(spec["anchor_row"])
    sha256 = str(spec["sha256"])
    object_key = str(spec["object_key"])
    model = str(spec["alt_text"])
    anchor_to_row = int(spec["anchor_to_row"])

    admin = db.scalar(select(AdminUser).limit(1))
    if admin is None:
        admin = AdminUser(
            email="primaries@example.com",
            password_hash=hash_password("correct-horse-1"),
            role="admin",
        )
        db.add(admin)
        db.flush()

    brand = Brand(slug=f"brand-{slug}"[:60], is_published=True)
    db.add(brand)
    db.flush()
    db.add(BrandTranslation(brand_id=brand.id, locale="en", name="HiLook"))
    category = Category(slug=f"cat-{slug}"[:60], is_published=True, sort_order=0)
    db.add(category)
    db.flush()
    db.add(CategoryTranslation(category_id=category.id, locale="en", name="Cameras"))
    product = Product(
        slug=slug,
        brand_id=brand.id,
        category_id=category.id,
        model_display=model,
        model_raw=model,
        model_normalized=model.lower(),
        catalog_status="published",
        stock_status="in_stock",
        public_price_status="on_request",
        product_kind="product",
    )
    db.add(product)
    db.flush()
    db.add(
        ProductTranslation(
            product_id=product.id,
            locale="en",
            localized_name=model,
            description=f"Description for {model}",
            origin="manual",
        )
    )
    db.add(
        ProductTranslation(
            product_id=product.id,
            locale="ru",
            localized_name=model,
            description=f"RU {model}",
            origin="manual",
        )
    )
    job = ImportJob(
        created_by=admin.id,
        status="applied",
        applied_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.flush()
    import_file = ImportFile(
        job_id=job.id,
        source_code="hikvision",
        original_filename="Hikvision pr.xlsx",
        sha256="a" * 64,
        stored_object_key=f"private-uploads/{job.id}",
    )
    db.add(import_file)
    db.flush()
    path = media_root / object_key
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        path.write_bytes(png_bytes(40))
    db.add(
        ImportAsset(
            import_file_id=import_file.id,
            object_key=object_key,
            sha256=sha256,
            mime_type="image/png",
            worksheet=worksheet,
            anchor_row=row,
            anchor_col=2,
            anchor_to_row=anchor_to_row,
            link_status="linked_high",
        )
    )
    db.add(
        ProductSourceRecord(
            product_id=product.id,
            source_code="hikvision",
            source_workbook="Hikvision pr.xlsx",
            source_worksheet=worksheet,
            source_row=row,
            source_model_raw=model,
            source_price_kind="blank",
            match_key=f"hikvision|{worksheet}|{row}|{slug}",
            first_job_id=job.id,
            last_job_id=job.id,
        )
    )
    db.commit()
    return product


def _clear_images(db: Session, product_id: int) -> None:
    db.execute(delete(ProductImage).where(ProductImage.product_id == product_id))
    db.commit()


def test_apply_is_idempotent_and_skips_manual_images(primaries_engine) -> None:
    engine, media_root, _database_url = primaries_engine
    slug = "hilook-ipc-b160ha-luf-sl"
    spec = SOURCE_BACKED_MISSING_PRIMARIES[slug]
    with Session(bind=engine) as db:
        product = _ensure_seeded(db, media_root, slug=slug)
        _clear_images(db, product.id)

    with engine.begin() as connection:
        first = apply_source_backed_missing_primaries(connection, media_root=media_root)
        second = apply_source_backed_missing_primaries(connection, media_root=media_root)
    assert first >= 1
    assert second == 0

    with Session(bind=engine) as db:
        product = db.scalar(
            select(Product).where(Product.slug == slug).options(selectinload(Product.images))
        )
        assert product is not None
        assert len(product.images) == 1
        image = product.images[0]
        assert image.sha256.strip() == spec["sha256"]
        assert image.is_primary is True
        assert image.association_status == "high"
        assert image.object_key == spec["object_key"]

        other_key = "objects/ab/" + ("c" * 64) + ".png"
        (media_root / other_key).parent.mkdir(parents=True, exist_ok=True)
        (media_root / other_key).write_bytes(png_bytes(41))
        product_id = product.id
        db.delete(image)
        db.commit()
        db.add(
            ProductImage(
                product_id=product_id,
                storage_backend="local",
                object_key=other_key,
                mime_type="image/png",
                byte_size=10,
                sha256="c" * 64,
                sort_order=0,
                is_primary=True,
                association_status="confirmed",
            )
        )
        db.commit()

    with engine.begin() as connection:
        blocked = apply_source_backed_missing_primaries(connection, media_root=media_root)
    assert blocked == 0


def test_apply_links_shared_checksum_to_both_intercom_rows(primaries_engine) -> None:
    engine, media_root, _database_url = primaries_engine
    slugs = ("hilook-ds-kis202t", "hilook-vdp-k203")
    with Session(bind=engine) as db:
        for slug in slugs:
            product = _ensure_seeded(db, media_root, slug=slug)
            _clear_images(db, product.id)

    with engine.begin() as connection:
        linked = apply_source_backed_missing_primaries(connection, media_root=media_root)
    assert linked >= 2

    with Session(bind=engine) as db:
        digests = set()
        keys = set()
        for slug in slugs:
            product = db.scalar(
                select(Product).where(Product.slug == slug).options(selectinload(Product.images))
            )
            assert product is not None
            assert len(product.images) == 1
            digests.add(product.images[0].sha256.strip())
            keys.add(product.images[0].object_key)
        assert digests == {
            "7ca0d55905dc5af2c347d9ea6034fb7c56afbf05830941177dff7c80fc372490"
        }
        assert keys == {
            "objects/7c/7ca0d55905dc5af2c347d9ea6034fb7c56afbf05830941177dff7c80fc372490.png"
        }


def test_revert_removes_only_matching_high_rows(primaries_engine) -> None:
    engine, media_root, _database_url = primaries_engine
    slug = "hikvision-ids-tcm403-b"
    with Session(bind=engine) as db:
        product = _ensure_seeded(db, media_root, slug=slug)
        _clear_images(db, product.id)
    with engine.begin() as connection:
        applied = apply_source_backed_missing_primaries(connection, media_root=media_root)
        cleared = revert_source_backed_missing_primaries(connection)
    assert applied >= 1
    assert cleared >= 1
    with Session(bind=engine) as db:
        product = db.scalar(
            select(Product).where(Product.slug == slug).options(selectinload(Product.images))
        )
        assert product is not None
        assert product.images == []


def test_public_api_returns_backfilled_image(primaries_engine) -> None:
    engine, media_root, database_url = primaries_engine
    slug = "hikvision-ds-2cd2t83g2-4li2u-4mm-black"
    spec = SOURCE_BACKED_MISSING_PRIMARIES[slug]
    with Session(bind=engine) as db:
        product = _ensure_seeded(db, media_root, slug=slug)
        _clear_images(db, product.id)
    with engine.begin() as connection:
        apply_source_backed_missing_primaries(connection, media_root=media_root)

    settings = Settings(
        database_url=database_url,
        session_secret="test-only-secret",
        media_root=str(media_root),
        media_public_base_url="http://test/media",
        public_site_url="http://testserver",
        app_env="local",
    )
    get_settings.cache_clear()
    app = create_app(settings)
    with TestClient(app) as client:
        detail = client.get(f"/api/public/products/{slug}", params={"locale": "en"}).json()
        assert detail["image"]["url"] == f"/media/{spec['object_key']}"
        assert detail["image"]["alt"]
        assert detail["images"][0]["url"] == f"/media/{spec['object_key']}"
    get_settings.cache_clear()
