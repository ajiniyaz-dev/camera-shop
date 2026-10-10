import os
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.importing.stage import SourceInput, StagingError, stage_import
from app.models import (
    AdminUser,
    Brand,
    BrandTranslation,
    Category,
    CategoryTranslation,
    ImportAsset,
    ImportFile,
    ImportJob,
    ImportRow,
    Product,
    ProductSourceRecord,
    ProductTranslation,
)
from tests.import_builders import ezviz_workbook, hikvision_workbook, single_hikvision_row

API_ROOT = Path(__file__).resolve().parents[1]
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
    pytest.fail("PostgreSQL is not reachable for the disposable Phase 4A database")


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


@pytest.fixture(scope="module")
def schema_engine():
    admin_url, admin_engine = _admin_engine()
    database_url = _recreate(admin_engine, "catalog_phase4a_test", admin_url)
    previous = os.environ.get("DATABASE_URL")
    try:
        command.upgrade(_alembic(database_url), "head")
        engine = create_engine(database_url)
        yield engine
        engine.dispose()
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()
        with admin_engine.connect() as connection:
            connection.execute(text('DROP DATABASE IF EXISTS "catalog_phase4a_test" WITH (FORCE)'))
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


def _job(session: Session, **overrides: object) -> ImportJob:
    admin = AdminUser(email="stage@example.com", password_hash="stored-hash", role="admin")
    session.add(admin)
    session.flush()
    job = ImportJob(created_by=admin.id, **overrides)
    session.add(job)
    session.flush()
    return job


def _catalog_snapshot(session: Session) -> list[tuple[object, ...]]:
    return list(
        session.execute(
            select(
                Product.id,
                Product.public_price_amount,
                Product.public_price_status,
                Product.model_display,
                Product.stock_status,
                Product.catalog_status,
                ProductSourceRecord.match_key,
                ProductSourceRecord.source_price_amount,
                ProductSourceRecord.absent_from_latest,
            )
            .join(ProductSourceRecord, ProductSourceRecord.product_id == Product.id, isouter=True)
            .order_by(Product.id)
        ).all()
    )


def test_stages_one_or_both_workbooks_without_publishing(db: Session, tmp_path: Path) -> None:
    hikvision = tmp_path / "Hikvision pr.xlsx"
    ezviz = tmp_path / "Ezviz pr.xlsx"
    hikvision_workbook(hikvision)
    ezviz_workbook(ezviz)
    media = tmp_path / "media"
    job = _job(db)
    before = db.scalar(select(func.count()).select_from(Product))
    summary = stage_import(
        db,
        job,
        [
            SourceInput(hikvision, "Hikvision pr.xlsx"),
            SourceInput(ezviz, "Ezviz pr.xlsx"),
        ],
        media,
    )
    db.flush()
    assert job.status == "preview"
    assert job.applied_at is None
    assert db.scalar(select(func.count()).select_from(Product)) == before
    assert set(db.scalars(select(ImportFile.source_code))) == {"hikvision", "ezviz"}
    assert db.scalar(select(func.count()).select_from(ImportRow).where(ImportRow.applied.is_(True))) == 0
    assert summary["combined"]["product"] > 0
    assert summary["combined"]["service"] == 2
    assert (media / "imports" / str(job.id) / "hikvision.xlsx").is_file()
    stored = list((media / "objects").rglob("*.png"))
    assert stored
    assert all(path.parent.name == path.name[:2] for path in stored)
    priced = db.scalars(select(ImportRow).where(ImportRow.classification == "product")).all()
    assert any(row.proposal["price"]["amount"] == "115.00" for row in priced)
    assert any(row.proposal["price"]["kind"] == "blank" for row in priced)
    assert any(row.proposal["price"]["kind"] == "explicit_on_request" for row in priced)


def test_retry_replaces_staged_rows_instead_of_duplicating_them(db: Session, tmp_path: Path) -> None:
    path = tmp_path / "Hikvision pr.xlsx"
    hikvision_workbook(path)
    media = tmp_path / "media"
    job = _job(db)
    stage_import(db, job, [SourceInput(path, path.name)], media)
    db.flush()
    first = db.scalar(select(func.count()).select_from(ImportRow))
    assets = db.scalar(select(func.count()).select_from(ImportAsset))
    stage_import(db, job, [SourceInput(path, path.name)], media)
    db.flush()
    assert db.scalar(select(func.count()).select_from(ImportRow)) == first
    assert db.scalar(select(func.count()).select_from(ImportAsset)) == assets
    assert db.scalar(select(func.count()).select_from(ImportFile)) == 1


def test_filename_disagreement_does_not_stage_either_source(db: Session, tmp_path: Path) -> None:
    path = tmp_path / "Ezviz pr.xlsx"
    hikvision_workbook(path)
    job = _job(db)
    summary = stage_import(db, job, [SourceInput(path, path.name)], tmp_path / "media")
    assert summary["rejected_files"][0]["code"] == "filename_signature_disagreement"
    assert db.scalar(select(func.count()).select_from(ImportFile)) == 0
    assert db.scalar(select(func.count()).select_from(ImportRow)) == 0


def test_admin_confirmation_stages_the_declared_source(db: Session, tmp_path: Path) -> None:
    path = tmp_path / "Ezviz pr.xlsx"
    hikvision_workbook(path)
    job = _job(db)
    stage_import(
        db,
        job,
        [
            SourceInput(
                path,
                path.name,
                identification="admin_confirmed",
                declared_source="hikvision",
            )
        ],
        tmp_path / "media",
    )
    db.flush()
    stored = db.scalars(select(ImportFile)).one()
    assert stored.source_code == "hikvision"
    assert stored.identification == "admin_confirmed"
    assert stored.validation_status == "valid"


def test_matching_preserves_manual_values_and_live_rows(db: Session, tmp_path: Path) -> None:
    path = tmp_path / "Hikvision pr.xlsx"
    single_hikvision_row(path, price=40)
    media = tmp_path / "media"
    job = _job(db)
    brand = Brand(slug="hikvision", is_published=True)
    category = Category(slug="nvr", sort_order=0, is_published=True, source_code="hikvision")
    db.add_all([brand, category])
    db.flush()
    db.add_all(
        [
            BrandTranslation(brand_id=brand.id, locale="ru", name="Hikvision"),
            CategoryTranslation(category_id=category.id, locale="ru", name="NVR"),
        ]
    )
    product = Product(
        brand_id=brand.id,
        category_id=category.id,
        product_kind="product",
        model_raw="Hikvision NVR-1",
        model_display="Hikvision NVR-1",
        model_normalized="hikvision nvr-1",
        public_price_status="numeric",
        public_price_amount=Decimal("40.00"),
        public_currency="USD",
        slug="hikvision-nvr-1",
        catalog_status="published",
        stock_status="in_stock",
        price_locked=True,
    )
    db.add(product)
    db.flush()
    db.add(
        ProductTranslation(
            product_id=product.id,
            locale="ru",
            description="регистратор",
            origin="manual",
            description_locked=False,
        )
    )
    from app.importing.normalize import build_match_key, description_sha256

    db.add(
        ProductSourceRecord(
            product_id=product.id,
            source_code="hikvision",
            source_workbook="Hikvision pr.xlsx",
            source_worksheet="NVR",
            source_row=2,
            source_model_raw="Hikvision NVR-1",
            source_description_raw="регистратор",
            source_price_header="Цена",
            source_price_kind="numeric",
            source_price_amount=Decimal("40.00"),
            match_key=build_match_key(
                "hikvision",
                "NVR",
                "hikvision nvr-1",
                "",
                description_sha256("регистратор"),
            ),
            first_job_id=job.id,
            last_job_id=job.id,
        )
    )
    other = Product(
        product_kind="product",
        model_raw="CS-1",
        model_display="CS-1",
        model_normalized="cs-1",
        public_price_status="numeric",
        public_price_amount=Decimal("9.00"),
        public_currency="USD",
        slug="ezviz-cs-1",
        catalog_status="published",
    )
    db.add(other)
    db.flush()
    db.add(
        ProductSourceRecord(
            product_id=other.id,
            source_code="ezviz",
            source_workbook="Ezviz pr.xlsx",
            source_worksheet="Ezviz",
            source_row=3,
            source_model_raw="CS-1",
            source_price_kind="numeric",
            source_price_amount=Decimal("9.00"),
            match_key="ezviz-separate",
            first_job_id=job.id,
            last_job_id=job.id,
        )
    )
    db.flush()
    before = _catalog_snapshot(db)

    unchanged = stage_import(db, job, [SourceInput(path, "Hikvision pr.xlsx")], media)
    db.flush()
    same = db.scalars(select(ImportRow).where(ImportRow.classification == "product")).one()
    assert same.action == "unchanged"
    assert same.matched_product_id == product.id
    assert unchanged["sources"][0]["counts"]["unchanged"] == 1

    single_hikvision_row(path, price=55)
    summary = stage_import(db, job, [SourceInput(path, "Hikvision pr.xlsx")], media)
    db.flush()
    db.refresh(product)
    db.refresh(other)
    assert product.public_price_amount == Decimal("40.00")
    assert other.public_price_amount == Decimal("9.00")
    assert _catalog_snapshot(db) == before
    staged = db.scalars(select(ImportRow).where(ImportRow.classification == "product")).one()
    assert staged.action == "update"
    assert staged.resolution == "keep_current"
    assert staged.matched_product_id == product.id
    assert staged.proposal["field_resolutions"]["public_price"] == "keep_current"
    assert staged.applied is False
    assert summary["sources"][0]["absent_product_ids"] == []

    job.replace_prices = True
    stage_import(db, job, [SourceInput(path, "Hikvision pr.xlsx")], media)
    db.flush()
    db.refresh(product)
    staged = db.scalars(select(ImportRow).where(ImportRow.classification == "product")).one()
    assert staged.proposal["field_resolutions"]["public_price"] == "accept_excel"
    assert product.public_price_amount == Decimal("40.00")


def test_possible_match_stays_pending_and_does_not_merge(db: Session, tmp_path: Path) -> None:
    path = tmp_path / "Hikvision pr.xlsx"
    single_hikvision_row(path)
    job = _job(db)
    product = Product(
        product_kind="product",
        model_raw="Hikvision NVR-1",
        model_display="Hikvision NVR-1",
        model_normalized="hikvision nvr-1",
        public_price_status="numeric",
        public_price_amount=Decimal("40.00"),
        public_currency="USD",
        slug="possible-nvr",
        catalog_status="draft",
    )
    db.add(product)
    db.flush()
    db.add(
        ProductTranslation(
            product_id=product.id,
            locale="ru",
            description="старое описание",
            origin="source",
        )
    )
    from app.importing.normalize import build_match_key, description_sha256

    db.add(
        ProductSourceRecord(
            product_id=product.id,
            source_code="hikvision",
            source_workbook="old.xlsx",
            source_worksheet="NVR",
            source_row=9,
            source_model_raw="Hikvision NVR-1",
            source_price_kind="numeric",
            source_price_amount=Decimal("40.00"),
            match_key=build_match_key(
                "hikvision",
                "NVR",
                "hikvision nvr-1",
                "",
                description_sha256("старое описание"),
            ),
            first_job_id=job.id,
            last_job_id=job.id,
        )
    )
    db.flush()
    stage_import(db, job, [SourceInput(path, path.name)], tmp_path / "media")
    db.flush()
    staged = db.scalars(select(ImportRow).where(ImportRow.classification == "product")).one()
    assert staged.action == "possible_match"
    assert staged.resolution == "pending"
    assert staged.matched_product_id == product.id
    db.refresh(product)
    assert product.model_display == "Hikvision NVR-1"
    assert db.scalar(select(func.count()).select_from(Product)) == 1


def test_failed_flush_removes_new_files_and_leaves_the_catalog(db: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "Hikvision pr.xlsx"
    hikvision_workbook(path)
    media = tmp_path / "media"
    job = _job(db)
    product = Product(
        product_kind="product",
        model_raw="kept",
        model_display="kept",
        model_normalized="kept",
        public_price_status="on_request",
        slug="kept-product",
        catalog_status="published",
    )
    db.add(product)
    db.flush()

    def fail_flush(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("flush failed")

    monkeypatch.setattr(db, "flush", fail_flush)
    with pytest.raises(RuntimeError, match="flush failed"):
        stage_import(db, job, [SourceInput(path, path.name)], media)
    monkeypatch.undo()
    assert product.public_price_status == "on_request"
    assert list(media.rglob("*.png"))
    assert list(media.rglob("*.xlsx")) == []


def test_media_root_cannot_be_the_source_directory(db: Session, tmp_path: Path) -> None:
    source_dir = tmp_path / "data" / "source"
    source_dir.mkdir(parents=True)
    path = source_dir / "Hikvision pr.xlsx"
    single_hikvision_row(path)
    job = _job(db)
    with pytest.raises(StagingError):
        stage_import(db, job, [SourceInput(path, path.name)], source_dir)
