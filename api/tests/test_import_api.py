import os
import threading
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
from app.importing.apply import apply_job
from app.main import create_app
from app.models import AdminUser, ImportJob, ImportRow, Product, ProductImage, ProductSourceRecord, ProductTranslation
from tests.import_builders import (
    ezviz_workbook,
    hikvision_workbook,
    single_hikvision_row,
    workbook_with_duplicate_model,
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
        assert dealer.public_price_amount == Decimal("92.50")
        assert dealer.public_currency == "USD"
        assert dealer.stock_status == "in_stock"
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
        assert priced.public_price_amount == Decimal("115.00")
        assert db.scalar(select(func.count()).select_from(ProductImage).where(ProductImage.product_id == priced.id)) >= 1
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
        json={"resolution": "accept_excel"},
        headers=headers,
    )
    assert resolved.status_code == 200
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
