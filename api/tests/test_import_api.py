import os
import threading
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session, selectinload

from app.auth.passwords import hash_password
from app.config import Settings, get_settings
from app.importing.apply import apply_job
from app.main import create_app
from app.models import (
    AdminUser,
    Brand,
    BrandTranslation,
    Category,
    CategoryTranslation,
    ImportJob,
    ImportRow,
    Product,
    ProductImage,
    ProductSourceRecord,
    ProductTranslation,
)
from tests.import_builders import (
    ezviz_workbook,
    hikvision_workbook,
    single_hikvision_row,
    workbook_with_duplicate_model,
    workbook_with_off_column_photo,
)

API_ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct-horse-1"
ORIGIN = {"Origin": "http://testserver"}
MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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
    pytest.fail("PostgreSQL is not reachable for the disposable Phase 4B database")


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


def _settings(database_url: str, media_root: Path, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": database_url,
        "session_secret": "test-only-secret",
        "app_env": "local",
        "debug": False,
        "public_site_url": "http://testserver",
        "media_root": str(media_root),
    }
    values.update(overrides)
    return Settings(**values)


@pytest.fixture(scope="module")
def database_url():
    admin_url, admin_engine = _admin_engine()
    url = _recreate(admin_engine, "catalog_phase4b_test", admin_url)
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
            connection.execute(text('DROP DATABASE IF EXISTS "catalog_phase4b_test" WITH (FORCE)'))
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
                  product_images, product_translations, product_source_records, products,
                  import_jobs, category_translations, categories, brand_translations, brands,
                  admin_users
                RESTART IDENTITY CASCADE
                """
            )
        )
    yield db_engine
    db_engine.dispose()


@pytest.fixture
def media_root(tmp_path: Path) -> Path:
    root = tmp_path / "media"
    root.mkdir()
    return root


@pytest.fixture
def client(engine, database_url: str, media_root: Path):
    application = create_app(_settings(database_url, media_root))
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
        headers=ORIGIN,
    )
    assert response.status_code == 200
    return {"Origin": "http://testserver", "X-CSRF-Token": response.json()["csrf_token"]}


def _upload(client: TestClient, headers: dict[str, str], path: Path, **data: str):
    return client.post(
        "/api/admin/imports",
        files={"files": (path.name, path.read_bytes(), MIME)},
        data=data,
        headers=headers,
    )


def test_upload_requires_authentication_and_csrf(client: TestClient, engine, tmp_path: Path) -> None:
    _seed(engine)
    path = tmp_path / "Hikvision pr.xlsx"
    single_hikvision_row(path)
    anonymous = _upload(client, {}, path)
    assert anonymous.status_code == 401
    logged_in = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": PASSWORD},
        headers=ORIGIN,
    )
    missing_csrf = _upload(client, {"Origin": "http://testserver"}, path)
    assert missing_csrf.status_code == 403
    assert "password" not in logged_in.text


def test_hikvision_ezviz_and_both_uploads(client: TestClient, engine, media_root: Path, tmp_path: Path) -> None:
    _seed(engine)
    headers = _auth(client)
    hikvision = tmp_path / "Hikvision pr.xlsx"
    ezviz = tmp_path / "Ezviz pr.xlsx"
    single_hikvision_row(hikvision)
    ezviz_workbook(ezviz)
    only_hikvision = _upload(client, headers, hikvision)
    assert only_hikvision.status_code == 200
    assert only_hikvision.json()["files"][0]["source_code"] == "hikvision"
    assert str(media_root) not in only_hikvision.text
    only_ezviz = _upload(client, headers, ezviz)
    assert only_ezviz.status_code == 200
    assert only_ezviz.json()["files"][0]["source_code"] == "ezviz"
    both = client.post(
        "/api/admin/imports",
        files=[
            ("files", ("Hikvision pr.xlsx", hikvision.read_bytes(), MIME)),
            ("files", ("Ezviz pr.xlsx", ezviz.read_bytes(), MIME)),
        ],
        headers=headers,
    )
    assert both.status_code == 200
    body = both.json()
    assert {item["source_code"] for item in body["files"]} == {"hikvision", "ezviz"}
    assert body["summary"]["combined"]["service"] == 2
    assert (media_root / "imports" / str(body["id"]) / "hikvision.xlsx").is_file()
    assert not (media_root / "private-uploads").exists() or not any((media_root / "private-uploads").iterdir())


def test_rejects_malformed_oversized_and_signature_mismatch(
    engine, database_url: str, media_root: Path, tmp_path: Path
) -> None:
    _seed(engine)
    application = create_app(_settings(database_url, media_root, import_max_bytes=32_768))
    with TestClient(application) as client:
        headers = _auth(client)
        malformed = tmp_path / "Hikvision pr.xlsx"
        malformed.write_bytes(b"this is not a workbook")
        rejected = _upload(client, headers, malformed)
        assert rejected.status_code == 422
        mismatch = tmp_path / "Ezviz pr.xlsx"
        single_hikvision_row(mismatch)
        disagreed = _upload(client, headers, mismatch)
        assert disagreed.status_code == 422
        assert disagreed.json()["detail"]["rejected_files"][0]["code"] == "filename_signature_disagreement"
        confirmed = client.post(
            "/api/admin/imports",
            files={"files": (mismatch.name, mismatch.read_bytes(), MIME)},
            data={"source_overrides": "hikvision"},
            headers=headers,
        )
        assert confirmed.status_code == 200
        assert confirmed.json()["files"][0]["source_code"] == "hikvision"
        oversized = client.post(
            "/api/admin/imports",
            files={"files": ("Hikvision pr.xlsx", b"x" * 40_000, MIME)},
            headers=headers,
        )
        assert oversized.status_code == 413
    application.state.engine.dispose()


def test_preview_pagination_and_row_ownership(client: TestClient, engine, tmp_path: Path) -> None:
    _seed(engine)
    headers = _auth(client)
    path = tmp_path / "Hikvision pr.xlsx"
    hikvision_workbook(path)
    created = _upload(client, headers, path)
    assert created.status_code == 200
    job_id = created.json()["id"]
    preview = client.get(f"/api/admin/imports/{job_id}", headers=ORIGIN)
    assert preview.status_code == 200
    assert preview.json()["summary"]["combined"]["heading"] == 2
    page = client.get(f"/api/admin/imports/{job_id}/rows", params={"page": 1, "page_size": 1}, headers=ORIGIN)
    assert page.status_code == 200
    assert page.json()["total"] > 1
    assert len(page.json()["rows"]) == 1
    assert "proposal" in page.json()["rows"][0]
    assert "current" in page.json()["rows"][0]
    assets = client.get(f"/api/admin/imports/{job_id}/assets", params={"page": 1, "page_size": 1}, headers=ORIGIN)
    assert assets.status_code == 200
    assert assets.json()["page"] == 1
    assert "total" in assets.json()
    assert len(assets.json()["assets"]) <= 1
    other = _upload(client, headers, path)
    foreign_row = page.json()["rows"][0]["id"]
    crossed = client.patch(
        f"/api/admin/imports/{other.json()['id']}/rows/{foreign_row}",
        json={"resolution": "exclude"},
        headers=headers,
    )
    assert crossed.status_code == 404


def test_apply_prices_images_and_idempotency(client: TestClient, engine, media_root: Path, tmp_path: Path) -> None:
    _seed(engine)
    headers = _auth(client)
    hikvision = tmp_path / "Hikvision pr.xlsx"
    ezviz = tmp_path / "Ezviz pr.xlsx"
    hikvision_workbook(hikvision)
    ezviz_workbook(ezviz)
    created = client.post(
        "/api/admin/imports",
        files=[
            ("files", ("Hikvision pr.xlsx", hikvision.read_bytes(), MIME)),
            ("files", ("Ezviz pr.xlsx", ezviz.read_bytes(), MIME)),
        ],
        headers=headers,
    )
    job_id = created.json()["id"]
    blocked = client.post(f"/api/admin/imports/{job_id}/apply", json={}, headers=headers)
    assert blocked.status_code == 422
    applied = client.post(f"/api/admin/imports/{job_id}/apply", json={"confirm": True}, headers=headers)
    assert applied.status_code == 200
    assert applied.json()["status"] == "applied"
    db = Session(bind=engine)
    try:
        dealer = db.scalar(select(Product).where(Product.model_display == "CS-DP2C"))
        assert dealer is not None
        assert dealer.product_kind == "product"
        assert dealer.catalog_status == "published"
        assert dealer.public_price_amount == Decimal("92.50")
        assert dealer.public_currency == "USD"
        assert dealer.stock_status == "in_stock"
        services = db.scalars(select(Product).where(Product.product_kind == "service")).all()
        assert len(services) == 2
        assert {item.catalog_status for item in services} == {"draft"}
        assert {item.model_display for item in services} == {"7-дневная видеоистория событий"}
        blank = db.scalar(
            select(ProductSourceRecord).where(ProductSourceRecord.source_price_kind == "blank")
        )
        explicit = db.scalar(
            select(ProductSourceRecord).where(ProductSourceRecord.source_price_kind == "explicit_on_request")
        )
        assert blank is not None and blank.source_price_amount is None
        assert explicit is not None and explicit.source_price_amount is None
        priced = db.scalar(select(Product).where(Product.model_display == "HiLook IPC-1"))
        assert priced is not None
        assert priced.product_kind == "product"
        assert priced.catalog_status == "published"
        assert priced.public_price_amount == Decimal("115.00")
        priced_ru = next(item for item in priced.translations if item.locale == "ru")
        assert priced_ru.localized_name == "HiLook IPC-1"
        assert priced_ru.description == "уличная камера"
        assert {item.locale for item in priced.translations} == {"ru"}
        for service in services:
            service_ru = next(item for item in service.translations if item.locale == "ru")
            assert service_ru.localized_name == service.model_display
            assert service.option_label in {"Ежемесячно:", "Ежегодно:"}
            assert service_ru.localized_name != service.option_label
            assert {item.locale for item in service.translations} == {"ru"}
        assert db.scalar(select(func.count()).select_from(ProductImage).where(ProductImage.product_id == priced.id)) >= 1
        # Merged photo range: monthly owns linked_high; yearly is shared_candidate — both get the file.
        service_images = {
            item.option_label: db.scalars(
                select(ProductImage).where(ProductImage.product_id == item.id)
            ).all()
            for item in services
        }
        assert len(service_images["Ежемесячно:"]) == 1
        assert len(service_images["Ежегодно:"]) == 1
        monthly_img = service_images["Ежемесячно:"][0]
        yearly_img = service_images["Ежегодно:"][0]
        assert monthly_img.sha256 == yearly_img.sha256
        assert monthly_img.object_key == yearly_img.object_key
        assert monthly_img.is_primary and yearly_img.is_primary
        assert monthly_img.association_status == "high"
        assert yearly_img.association_status == "high"
        source = db.scalar(select(ProductSourceRecord).where(ProductSourceRecord.product_id == priced.id))
        assert source is not None
        assert source.internal_note == "текущая цена со скидкой 60$"
        assert source.first_job_id == job_id
        assert source.last_job_id == job_id
    finally:
        db.close()
    again = client.post(f"/api/admin/imports/{job_id}/apply", json={"confirm": True}, headers=headers)
    assert again.status_code == 200
    assert again.json()["id"] == job_id
    db = Session(bind=engine)
    try:
        assert db.scalar(select(func.count()).select_from(Product).where(Product.model_display == "HiLook IPC-1")) == 1
    finally:
        db.close()


def test_shared_candidate_image_is_public_for_each_associated_product(
    client: TestClient, engine, media_root: Path, tmp_path: Path
) -> None:
    """Client-approved: one verified Excel image may be primary on every merged-range product."""

    _seed(engine)
    headers = _auth(client)
    path = tmp_path / "Ezviz pr.xlsx"
    ezviz_workbook(path)
    created = _upload(client, headers, path)
    job_id = created.json()["id"]
    applied = client.post(f"/api/admin/imports/{job_id}/apply", json={"confirm": True}, headers=headers)
    assert applied.status_code == 200

    db = Session(bind=engine)
    try:
        services = db.scalars(
            select(Product)
            .where(Product.product_kind == "service")
            .options(selectinload(Product.images), selectinload(Product.translations))
        ).all()
        assert len(services) == 2
        digests = set()
        keys = set()
        for product in services:
            assert len(product.images) == 1
            image = product.images[0]
            assert image.association_status == "high"
            assert image.is_primary is True
            digests.add(image.sha256.strip())
            keys.add(image.object_key)
            assert (media_root / image.object_key).is_file()
        assert len(digests) == 1
        assert len(keys) == 1
        digest = next(iter(digests))
        key = next(iter(keys))
    finally:
        db.close()

    # Publish drafts and give each row a distinct English name so public alts differ.
    db = Session(bind=engine)
    try:
        expected_alts: dict[str, str] = {}
        for product in db.scalars(
            select(Product)
            .where(Product.product_kind == "service")
            .options(selectinload(Product.images), selectinload(Product.translations))
        ).all():
            product.catalog_status = "published"
            period = "monthly" if "Ежемесячно" in (product.option_label or "") else "yearly"
            en_name = f"7-day video event history ({period})"
            expected_alts[product.slug] = en_name
            product.images[0].alt_text = "общее фото"  # Cyrillic stored alt yields to Latin EN name
            en = next((item for item in product.translations if item.locale == "en"), None)
            if en is None:
                db.add(
                    ProductTranslation(
                        product_id=product.id,
                        locale="en",
                        localized_name=en_name,
                        description="shared history plan",
                        origin="manual",
                    )
                )
            else:
                en.localized_name = en_name
        db.commit()
    finally:
        db.close()

    for slug, expected_alt in expected_alts.items():
        detail = client.get(f"/api/public/products/{slug}", params={"locale": "en"}).json()
        assert detail["image"]["url"] == f"/media/{key}"
        assert detail["image"]["alt"] == expected_alt
        assert detail["images"][0]["url"] == f"/media/{key}"
        assert detail["images"][0]["alt"] == expected_alt


def test_linked_review_image_stays_unlinked_on_apply(
    client: TestClient, engine, tmp_path: Path
) -> None:
    _seed(engine)
    headers = _auth(client)
    path = tmp_path / "Hikvision pr.xlsx"
    workbook_with_off_column_photo(path)
    created = _upload(client, headers, path)
    job_id = created.json()["id"]
    preview = client.get(f"/api/admin/imports/{job_id}", headers=ORIGIN)
    assert preview.status_code == 200
    applied = client.post(f"/api/admin/imports/{job_id}/apply", json={"confirm": True}, headers=headers)
    assert applied.status_code == 200
    db = Session(bind=engine)
    try:
        product = db.scalar(select(Product).where(Product.model_display == "Hikvision NVR-Review"))
        assert product is not None
        assert db.scalar(select(func.count()).select_from(ProductImage).where(ProductImage.product_id == product.id)) == 0
    finally:
        db.close()


def test_publish_new_products_false_inserts_equipment_as_draft(
    client: TestClient, engine, tmp_path: Path
) -> None:
    _seed(engine)
    headers = _auth(client)
    path = tmp_path / "Hikvision pr.xlsx"
    single_hikvision_row(path)
    created = _upload(client, headers, path, publish_new_products="false", replace_prices="false")
    assert created.status_code == 200
    assert created.json()["publish_new_products"] is False
    assert created.json()["replace_prices"] is False
    applied = client.post(
        f"/api/admin/imports/{created.json()['id']}/apply",
        json={"confirm": True},
        headers=headers,
    )
    assert applied.status_code == 200
    db = Session(bind=engine)
    try:
        product = db.scalar(select(Product).where(Product.model_display == "Hikvision NVR-1"))
        assert product is not None
        assert product.product_kind == "product"
        assert product.catalog_status == "draft"
        assert product.public_price_amount == Decimal("40.00")
        russian = next(item for item in product.translations if item.locale == "ru")
        assert russian.localized_name == "Hikvision NVR-1"
        assert russian.description == "регистратор"
        assert russian.origin == "source"
        assert {item.locale for item in product.translations} == {"ru"}
    finally:
        db.close()


def test_source_localized_name_uses_the_model_and_skips_a_blank_model() -> None:
    from app.importing.apply import _source_localized_name

    assert _source_localized_name({"model_display": " 12V 10A "}) == "12V 10A"
    assert _source_localized_name({"model_display": "   "}) is None
    assert _source_localized_name({"model_display": None}) is None


def test_reapply_keeps_a_manual_name_and_fills_a_blank_source_name(
    client: TestClient, engine, tmp_path: Path
) -> None:
    _seed(engine)
    headers = _auth(client)
    path = tmp_path / "Hikvision pr.xlsx"
    single_hikvision_row(path)

    def apply_workbook(price: int) -> None:
        single_hikvision_row(path, price=price)
        created = _upload(client, headers, path, publish_new_products="false", replace_prices="false")
        assert created.status_code == 200
        applied = client.post(
            f"/api/admin/imports/{created.json()['id']}/apply",
            json={"confirm": True},
            headers=headers,
        )
        assert applied.status_code == 200

    apply_workbook(40)
    db = Session(bind=engine)
    try:
        product = db.scalar(select(Product).where(Product.model_display == "Hikvision NVR-1"))
        assert product is not None
        russian = next(item for item in product.translations if item.locale == "ru")
        russian.localized_name = "Staff title"
        russian.origin = "manual"
        db.commit()
        product_id = product.id
    finally:
        db.close()
    apply_workbook(55)
    db = Session(bind=engine)
    try:
        product = db.get(Product, product_id)
        assert product is not None
        assert db.scalar(select(func.count()).select_from(Product)) == 1
        russian = next(item for item in product.translations if item.locale == "ru")
        assert russian.localized_name == "Staff title"
        assert russian.description == "регистратор"
        assert product.public_price_amount == Decimal("55.00")
        russian.localized_name = None
        russian.origin = "source"
        db.commit()
    finally:
        db.close()
    apply_workbook(60)
    db = Session(bind=engine)
    try:
        product = db.get(Product, product_id)
        assert product is not None
        russian = next(item for item in product.translations if item.locale == "ru")
        assert russian.localized_name == "Hikvision NVR-1"
        assert russian.description == "регистратор"
        assert product.model_raw == "Hikvision NVR-1"
        assert product.public_price_amount == Decimal("60.00")
        assert {item.locale for item in product.translations} == {"ru"}
    finally:
        db.close()


def test_manual_values_absent_products_and_resolution(client: TestClient, engine, tmp_path: Path) -> None:
    _seed(engine)
    headers = _auth(client)
    first_path = tmp_path / "Hikvision pr.xlsx"
    single_hikvision_row(first_path, price=40)
    first = _upload(client, headers, first_path)
    applied = client.post(
        f"/api/admin/imports/{first.json()['id']}/apply",
        json={"confirm": True},
        headers=headers,
    )
    assert applied.status_code == 200
    db = Session(bind=engine)
    try:
        product = db.scalar(select(Product).where(Product.model_display == "Hikvision NVR-1"))
        assert product is not None
        product.public_price_amount = Decimal("77.00")
        product.price_locked = True
        translation = db.scalar(select(ProductTranslation).where(ProductTranslation.product_id == product.id))
        source = db.scalar(select(ProductSourceRecord).where(ProductSourceRecord.product_id == product.id))
        assert translation is not None and source is not None
        translation.description = "changed by staff"
        source.source_description_raw = "changed by staff"
        source.source_description_sha256 = "ab" * 32
        source.match_key = source.match_key + "-old"
        db.commit()
        product_id = product.id
    finally:
        db.close()
    second = _upload(client, headers, first_path)
    job_id = second.json()["id"]
    refused = client.post(f"/api/admin/imports/{job_id}/apply", json={"confirm": True}, headers=headers)
    assert refused.status_code == 409
    db = Session(bind=engine)
    try:
        product = db.get(Product, product_id)
        assert product is not None
        assert product.public_price_amount == Decimal("77.00")
        row = db.scalar(select(ImportRow).where(ImportRow.action == "possible_match"))
        assert row is not None
        row_id = row.id
    finally:
        db.close()
    resolved = client.patch(
        f"/api/admin/imports/{job_id}/rows/{row_id}",
        json={"resolution": "accept_excel", "field": "public_price", "field_resolution": "accept_excel"},
        headers=headers,
    )
    assert resolved.status_code == 200
    assert resolved.json()["proposal"]["field_resolutions"]["public_price"] == "accept_excel"
    applied = client.post(f"/api/admin/imports/{job_id}/apply", json={"confirm": True}, headers=headers)
    assert applied.status_code == 200
    db = Session(bind=engine)
    try:
        assert db.scalar(select(func.count()).select_from(Product)) == 1
        product = db.get(Product, product_id)
        assert product is not None
        assert product.public_price_amount == Decimal("40.00")
        replacement = tmp_path / "other.xlsx"
        single_hikvision_row(replacement, model="Hikvision NVR-2", price=12)
    finally:
        db.close()
    third = _upload(client, headers, replacement)
    client.post(f"/api/admin/imports/{third.json()['id']}/apply", json={"confirm": True}, headers=headers)
    db = Session(bind=engine)
    try:
        kept = db.get(Product, product_id)
        assert kept is not None
        assert kept.catalog_status == "published"
        source = db.scalar(select(ProductSourceRecord).where(ProductSourceRecord.product_id == product_id))
        assert source is not None and source.absent_from_latest is True
        assert db.scalar(select(func.count()).select_from(Product)) == 2
    finally:
        db.close()


def test_failed_apply_rolls_back_and_concurrent_apply_is_single(
    client: TestClient, engine, media_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed(engine)
    headers = _auth(client)
    path = tmp_path / "Hikvision pr.xlsx"
    single_hikvision_row(path)
    created = _upload(client, headers, path)
    job_id = created.json()["id"]

    def explode(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("apply failed")

    monkeypatch.setattr("app.importing.apply._insert_product", explode)
    failed = client.post(f"/api/admin/imports/{job_id}/apply", json={"confirm": True}, headers=headers)
    assert failed.status_code == 409
    assert failed.json()["detail"] == "The import could not be applied."
    db = Session(bind=engine)
    try:
        assert db.scalar(select(func.count()).select_from(Product)) == 0
        job = db.get(ImportJob, job_id)
        assert job is not None and job.status == "failed"
    finally:
        db.close()
    monkeypatch.undo()

    created = _upload(client, headers, path)
    job_id = created.json()["id"]
    lookup = Session(bind=engine)
    try:
        admin_id = lookup.scalar(select(AdminUser.id))
    finally:
        lookup.close()
    errors: list[BaseException] = []

    def worker() -> None:
        session = Session(bind=engine)
        try:
            apply_job(session, job_id, int(admin_id), media_root)
            session.commit()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
            session.rollback()
        finally:
            session.close()

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    db = Session(bind=engine)
    try:
        assert db.scalar(select(func.count()).select_from(Product)) == 1
        assert db.get(ImportJob, job_id).status == "applied"
    finally:
        db.close()


def test_reject_and_asset_exclusion(client: TestClient, engine, tmp_path: Path) -> None:
    _seed(engine)
    headers = _auth(client)
    path = tmp_path / "Hikvision pr.xlsx"
    hikvision_workbook(path)
    created = _upload(client, headers, path)
    job_id = created.json()["id"]
    assets = client.get(f"/api/admin/imports/{job_id}/assets", headers=ORIGIN)
    assert assets.status_code == 200
    assert assets.json()["total"] >= 1
    asset_id = assets.json()["assets"][0]["id"]
    excluded = client.post(
        f"/api/admin/imports/{job_id}/assets/{asset_id}/exclusion",
        json={"excluded": True},
        headers=headers,
    )
    assert excluded.status_code == 200
    assert excluded.json()["excluded"] is True
    rejected = client.post(f"/api/admin/imports/{job_id}/reject", headers=headers)
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    again = client.post(f"/api/admin/imports/{job_id}/apply", json={"confirm": True}, headers=headers)
    assert again.status_code == 409
    changed = client.patch(
        f"/api/admin/imports/{job_id}/rows/1",
        json={"resolution": "exclude"},
        headers=headers,
    )
    assert changed.status_code == 409


def test_excluded_conflict_cannot_accept_one_excel_value(client: TestClient, engine, tmp_path: Path) -> None:
    _seed(engine)
    headers = _auth(client)
    path = tmp_path / "Hikvision pr.xlsx"
    workbook_with_duplicate_model(path)
    created = _upload(client, headers, path)
    assert created.status_code == 200
    job_id = created.json()["id"]
    db = Session(bind=engine)
    try:
        row = db.scalar(select(ImportRow).where(ImportRow.action == "conflict"))
        assert row is not None
        row_id = row.id
    finally:
        db.close()
    excluded = client.patch(
        f"/api/admin/imports/{job_id}/rows/{row_id}",
        json={"resolution": "exclude"},
        headers=headers,
    )
    assert excluded.status_code == 200
    accepted = client.patch(
        f"/api/admin/imports/{job_id}/rows/{row_id}",
        json={"resolution": "accept_excel"},
        headers=headers,
    )
    assert accepted.status_code == 409


def _rows(client: TestClient, headers: dict[str, str], job_id: int) -> list[dict]:
    page = client.get(f"/api/admin/imports/{job_id}/rows", params={"page_size": 100}, headers=headers)
    assert page.status_code == 200
    return page.json()["rows"]


def _apply_one(client: TestClient, headers: dict[str, str], path: Path):
    created = _upload(client, headers, path)
    assert created.status_code == 200
    job_id = created.json()["id"]
    applied = client.post(f"/api/admin/imports/{job_id}/apply", json={"confirm": True}, headers=headers)
    assert applied.status_code == 200
    return job_id


def test_row_accept_excel_does_not_override_a_locked_description(
    client: TestClient, engine, tmp_path: Path
) -> None:
    _seed(engine)
    headers = _auth(client)
    path = tmp_path / "Hikvision pr.xlsx"
    single_hikvision_row(path, model="SWITTEX 1,8m", price=3, description="Сетевой фильтр LOGA")
    _apply_one(client, headers, path)

    db = Session(bind=engine)
    try:
        product = db.scalar(select(Product))
        assert product is not None
        slug = product.slug
        filters = Category(slug="setevye-filtry", sort_order=1, is_published=True, source_code="hikvision")
        filters.translations.append(CategoryTranslation(locale="ru", name="Сетевые фильтры"))
        db.add(filters)
        db.flush()
        product.category_id = filters.id
        product.category_locked = True
        product.model_locked = True
        translation = next(item for item in product.translations if item.locale == "ru")
        translation.description = "SWITTEX 1,8m."
        translation.description_locked = True
        translation.origin = "manual"
        db.commit()
        product_id = product.id
    finally:
        db.close()

    created = _upload(client, headers, path)
    assert created.status_code == 200
    job_id = created.json()["id"]
    row = next(item for item in _rows(client, headers, created.json()["id"]) if item["action"] == "update")
    resolutions = row["proposal"]["field_resolutions"]
    assert resolutions["description"] == "keep_current"
    assert resolutions["category"] == "keep_current"
    accepted = client.patch(
        f"/api/admin/imports/{job_id}/rows/{row['id']}",
        json={"resolution": "accept_excel"},
        headers=headers,
    )
    assert accepted.status_code == 200
    kept = accepted.json()["proposal"]["field_resolutions"]
    assert kept["description"] == "keep_current"
    assert kept["category"] == "keep_current"
    applied = client.post(f"/api/admin/imports/{job_id}/apply", json={"confirm": True}, headers=headers)
    assert applied.status_code == 200

    db = Session(bind=engine)
    try:
        product = db.get(Product, product_id)
        assert product is not None
        assert product.slug == slug
        assert product.category_id is not None
        translation = next(item for item in product.translations if item.locale == "ru")
        assert translation.description == "SWITTEX 1,8m."
    finally:
        db.close()

    created = _upload(client, headers, path)
    row = next(item for item in _rows(client, headers, created.json()["id"]) if item["action"] == "update")
    approved = client.patch(
        f"/api/admin/imports/{created.json()['id']}/rows/{row['id']}",
        json={"resolution": "keep_current", "field": "description", "field_resolution": "accept_excel"},
        headers=headers,
    )
    assert approved.status_code == 200
    assert approved.json()["proposal"]["field_resolutions"]["description"] == "accept_excel"
    assert approved.json()["proposal"]["field_resolutions"]["category"] == "keep_current"
    applied = client.post(
        f"/api/admin/imports/{created.json()['id']}/apply", json={"confirm": True}, headers=headers
    )
    assert applied.status_code == 200
    db = Session(bind=engine)
    try:
        product = db.get(Product, product_id)
        assert product is not None
        assert product.slug == slug
        translation = next(item for item in product.translations if item.locale == "ru")
        assert translation.description == "Сетевой фильтр LOGA"
    finally:
        db.close()


def test_empty_brand_is_kept_until_an_explicit_field_decision(
    client: TestClient, engine, tmp_path: Path
) -> None:
    _seed(engine)
    headers = _auth(client)
    path = tmp_path / "Hikvision pr.xlsx"
    single_hikvision_row(path, model="камера 1", description="без кода")
    _apply_one(client, headers, path)
    db = Session(bind=engine)
    try:
        product = db.scalar(select(Product))
        assert product is not None
        brand = Brand(slug="hikvision", is_published=True)
        brand.translations.append(BrandTranslation(locale="ru", name="Hikvision"))
        db.add(brand)
        db.flush()
        product.brand_id = brand.id
        db.commit()
        product_id = product.id
        brand_id = brand.id
    finally:
        db.close()

    created = _upload(client, headers, path)
    row = next(item for item in _rows(client, headers, created.json()["id"]) if item["action"] == "update")
    assert row["proposal"]["field_resolutions"]["brand"] == "keep_current"
    assert any(item["code"] == "brand_absent" for item in row["messages"])
    applied = client.post(
        f"/api/admin/imports/{created.json()['id']}/apply", json={"confirm": True}, headers=headers
    )
    assert applied.status_code == 200
    db = Session(bind=engine)
    try:
        product = db.get(Product, product_id)
        assert product is not None
        assert product.brand_id == brand_id
    finally:
        db.close()

    created = _upload(client, headers, path)
    row = next(item for item in _rows(client, headers, created.json()["id"]) if item["action"] == "update")
    approved = client.patch(
        f"/api/admin/imports/{created.json()['id']}/rows/{row['id']}",
        json={"resolution": "keep_current", "field": "brand", "field_resolution": "accept_excel"},
        headers=headers,
    )
    assert approved.status_code == 200
    assert approved.json()["proposal"]["field_resolutions"]["brand"] == "accept_excel"
    applied = client.post(
        f"/api/admin/imports/{created.json()['id']}/apply", json={"confirm": True}, headers=headers
    )
    assert applied.status_code == 200
    db = Session(bind=engine)
    try:
        product = db.get(Product, product_id)
        assert product is not None
        assert product.brand_id is None
    finally:
        db.close()


def test_populated_source_brand_is_assigned(client: TestClient, engine, tmp_path: Path) -> None:
    _seed(engine)
    headers = _auth(client)
    path = tmp_path / "Hikvision pr.xlsx"
    single_hikvision_row(path, model="Hikvision DS-2CD", description="камера")
    _apply_one(client, headers, path)
    db = Session(bind=engine)
    try:
        product = db.scalar(select(Product))
        assert product is not None
        assert product.brand is not None
        assert any(item.name == "Hikvision" for item in product.brand.translations)
    finally:
        db.close()


def test_stale_manual_translations_are_flagged_and_kept(
    client: TestClient, engine, tmp_path: Path
) -> None:
    _seed(engine)
    headers = _auth(client)
    original = tmp_path / "Hikvision pr.xlsx"
    single_hikvision_row(original, description="регистратор")
    _apply_one(client, headers, original)
    changed = tmp_path / "Hikvision changed.xlsx"
    single_hikvision_row(changed, description="другой регистратор")
    created = _upload(client, headers, changed)
    row = next(item for item in _rows(client, headers, created.json()["id"]) if item["action"] == "possible_match")
    assert not any(item["code"] == "manual_translations_stale" for item in row["messages"])

    db = Session(bind=engine)
    try:
        product = db.scalar(select(Product))
        assert product is not None
        product.translations.append(
            ProductTranslation(locale="uz", description="qo'lda yozilgan", origin="manual", description_locked=True)
        )
        product.translations.append(
            ProductTranslation(locale="en", description="written by hand", origin="manual", description_locked=True)
        )
        db.commit()
        product_id = product.id
    finally:
        db.close()

    same = _upload(client, headers, original)
    same_row = next(item for item in _rows(client, headers, same.json()["id"]) if item["action"] == "unchanged")
    assert not any(item["code"] == "manual_translations_stale" for item in same_row["messages"])
    created = _upload(client, headers, changed)
    row = next(item for item in _rows(client, headers, created.json()["id"]) if item["action"] == "possible_match")
    warning = next(item for item in row["messages"] if item["code"] == "manual_translations_stale")
    assert warning["locales"] == ["en", "uz"]
    accepted = client.patch(
        f"/api/admin/imports/{created.json()['id']}/rows/{row['id']}",
        json={"resolution": "accept_excel"},
        headers=headers,
    )
    assert accepted.status_code == 200
    applied = client.post(
        f"/api/admin/imports/{created.json()['id']}/apply", json={"confirm": True}, headers=headers
    )
    assert applied.status_code == 200
    db = Session(bind=engine)
    try:
        product = db.get(Product, product_id)
        assert product is not None
        by_locale = {item.locale: item.description for item in product.translations}
        assert by_locale["ru"] == "другой регистратор"
        assert by_locale["uz"] == "qo'lda yozilgan"
        assert by_locale["en"] == "written by hand"
    finally:
        db.close()


def test_duplicate_source_rows_do_not_mark_the_product_absent(
    client: TestClient, engine, tmp_path: Path
) -> None:
    _seed(engine)
    headers = _auth(client)
    original = tmp_path / "Hikvision pr.xlsx"
    single_hikvision_row(original, description="один и тот же текст")
    _apply_one(client, headers, original)
    db = Session(bind=engine)
    try:
        product = db.scalar(select(Product))
        assert product is not None
        product.public_price_amount = Decimal("77.00")
        product.price_locked = True
        source = product.source_record
        assert source is not None
        source.absent_from_latest = True
        db.commit()
        product_id = product.id
    finally:
        db.close()

    duplicate = tmp_path / "Hikvision duplicate.xlsx"
    workbook_with_duplicate_model(duplicate)
    created = _upload(client, headers, duplicate)
    assert created.status_code == 200
    summary = created.json()["summary"]["sources"][0]
    assert summary["counts"]["conflict"] == 2
    assert summary["absent_product_ids"] == []
    rows = _rows(client, headers, created.json()["id"])
    conflicts = [row for row in rows if row["action"] == "conflict"]
    assert len(conflicts) == 2
    assert conflicts[0]["proposal"]["ambiguous_product_ids"] == [product_id]
    db = Session(bind=engine)
    try:
        product = db.get(Product, product_id)
        assert product is not None
        assert product.public_price_amount == Decimal("77.00")
        assert product.source_record is not None
        assert product.source_record.absent_from_latest is True
        assert db.scalar(select(func.count()).select_from(Product)) == 1
    finally:
        db.close()

    for row in conflicts:
        excluded = client.patch(
            f"/api/admin/imports/{created.json()['id']}/rows/{row['id']}",
            json={"resolution": "exclude"},
            headers=headers,
        )
        assert excluded.status_code == 200
    applied = client.post(
        f"/api/admin/imports/{created.json()['id']}/apply", json={"confirm": True}, headers=headers
    )
    assert applied.status_code == 200
    assert applied.json()["status"] == "applied"
    db = Session(bind=engine)
    try:
        product = db.get(Product, product_id)
        assert product is not None
        assert product.public_price_amount == Decimal("77.00")
        assert product.source_record is not None
        assert product.source_record.absent_from_latest is False
        assert db.scalar(select(func.count()).select_from(Product)) == 1
    finally:
        db.close()


def test_excluded_row_cannot_accept_one_field(client: TestClient, engine, tmp_path: Path) -> None:
    _seed(engine)
    headers = _auth(client)
    path = tmp_path / "Hikvision pr.xlsx"
    single_hikvision_row(path, price=40, description="регистратор")
    _apply_one(client, headers, path)
    changed = tmp_path / "Hikvision changed.xlsx"
    single_hikvision_row(changed, price=55, description="другой регистратор")
    created = _upload(client, headers, changed)
    row = next(item for item in _rows(client, headers, created.json()["id"]) if item["action"] == "possible_match")
    excluded = client.patch(
        f"/api/admin/imports/{created.json()['id']}/rows/{row['id']}",
        json={"resolution": "exclude"},
        headers=headers,
    )
    assert excluded.status_code == 200
    override = client.patch(
        f"/api/admin/imports/{created.json()['id']}/rows/{row['id']}",
        json={"resolution": "keep_current", "field": "description", "field_resolution": "accept_excel"},
        headers=headers,
    )
    assert override.status_code == 409
    assert override.json()["detail"] == "An excluded row cannot override one field."
    stored = next(item for item in _rows(client, headers, created.json()["id"]) if item["id"] == row["id"])
    assert stored["action"] == "exclude"
    applied = client.post(
        f"/api/admin/imports/{created.json()['id']}/apply", json={"confirm": True}, headers=headers
    )
    assert applied.status_code == 200
    db = Session(bind=engine)
    try:
        product = db.scalar(select(Product))
        assert product is not None
        translation = next(item for item in product.translations if item.locale == "ru")
        assert translation.description == "регистратор"
        assert product.public_price_amount == Decimal("40.00")
    finally:
        db.close()


def test_two_files_from_one_source_do_not_stage(client: TestClient, engine, tmp_path: Path) -> None:
    _seed(engine)
    headers = _auth(client)
    first = tmp_path / "Hikvision pr.xlsx"
    second = tmp_path / "Hikvision other.xlsx"
    single_hikvision_row(first)
    single_hikvision_row(second, model="Hikvision NVR-2")
    rejected = client.post(
        "/api/admin/imports",
        files=[
            ("files", (first.name, first.read_bytes(), MIME)),
            ("files", (second.name, second.read_bytes(), MIME)),
        ],
        headers=headers,
    )
    assert rejected.status_code == 422
    assert rejected.json()["detail"] == "A job can contain only one file for each source."
    db = Session(bind=engine)
    try:
        assert db.scalar(select(func.count()).select_from(Product)) == 0
        assert db.scalar(select(func.count()).select_from(ImportJob)) == 0
    finally:
        db.close()


def test_ezviz_category_case_reuses_the_existing_category(
    client: TestClient, engine, tmp_path: Path
) -> None:
    _seed(engine)
    headers = _auth(client)
    db = Session(bind=engine)
    try:
        category = Category(
            slug="ezviz", sort_order=0, is_published=True, source_code="ezviz", source_worksheet="Ezviz"
        )
        category.translations.append(CategoryTranslation(locale="ru", name="EZVIZ"))
        db.add(category)
        db.commit()
        category_id = category.id
    finally:
        db.close()
    path = tmp_path / "Ezviz pr.xlsx"
    ezviz_workbook(path)
    _apply_one(client, headers, path)
    db = Session(bind=engine)
    try:
        categories = db.scalars(select(Category)).all()
        assert len(categories) == 1
        stored = categories[0]
        assert stored.id == category_id
        assert stored.slug == "ezviz"
        assert stored.translations[0].name == "EZVIZ"
        products = db.scalars(select(Product)).all()
        assert products
        assert {product.category_id for product in products} == {category_id}
    finally:
        db.close()
