import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    AdminAuditLog,
    AdminUser,
    ImportAsset,
    ImportFile,
    ImportJob,
    ImportRow,
    Product,
    ProductSourceRecord,
)

API_ROOT = Path(__file__).resolve().parents[1]
ADMIN_URLS = [
    os.environ.get("PHASE2A_ADMIN_URL"),
    "postgresql+psycopg://catalog:change-me@127.0.0.1:5433/postgres",
    "postgresql+psycopg://catalog:catalog@127.0.0.1:5432/postgres",
]
SHA_A = "a" * 64
SHA_B = "b" * 64


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
    pytest.fail("PostgreSQL is not reachable for the disposable Phase 2B database")


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
    database_url = _recreate(admin_engine, "catalog_phase2b_test", admin_url)
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
            connection.execute(text('DROP DATABASE IF EXISTS "catalog_phase2b_test" WITH (FORCE)'))
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


def _admin(session: Session, email: str = "importer@example.com") -> AdminUser:
    admin = AdminUser(email=email, password_hash="stored-hash", role="admin")
    session.add(admin)
    session.flush()
    return admin


def _job(session: Session, admin: AdminUser, **overrides: object) -> ImportJob:
    values: dict[str, object] = {"created_by": admin.id}
    values.update(overrides)
    job = ImportJob(**values)
    session.add(job)
    session.flush()
    return job


def _file(session: Session, job: ImportJob, source_code: str, **overrides: object) -> ImportFile:
    values: dict[str, object] = {
        "job_id": job.id,
        "source_code": source_code,
        "original_filename": f"{source_code}.xlsx",
        "sha256": SHA_A if source_code == "hikvision" else SHA_B,
        "stored_object_key": f"imports/{job.id}/{source_code}.xlsx",
    }
    values.update(overrides)
    workbook = ImportFile(**values)
    session.add(workbook)
    session.flush()
    return workbook


def _product(session: Session, slug: str) -> Product:
    product = Product(
        product_kind="product",
        model_raw="E107",
        model_display="E107",
        model_normalized="e107",
        public_price_status="numeric",
        public_price_amount=Decimal("200.00"),
        public_currency="USD",
        price_locked=True,
        slug=slug,
        catalog_status="published",
        stock_status="in_stock",
    )
    session.add(product)
    session.flush()
    return product


def test_job_defaults_and_documented_statuses(db: Session) -> None:
    admin = _admin(db)
    job = _job(db, admin)
    db.refresh(job)
    assert job.status == "preview"
    assert job.replace_prices is False
    assert job.publish_new_products is True
    assert job.approved_by is None
    assert job.applied_at is None
    job.publish_new_products = False
    job.replace_prices = True
    db.flush()
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            _job(db, admin, status="uploaded")
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            _job(db, admin, status="completed", applied_at=datetime.now(timezone.utc))


def test_one_workbook_or_both_stay_independent(db: Session) -> None:
    admin = _admin(db)
    hikvision_only = _job(db, admin)
    _file(db, hikvision_only, "hikvision")
    ezviz_only = _job(db, admin)
    _file(db, ezviz_only, "ezviz", sha256=SHA_A)
    both = _job(db, admin)
    hikvision = _file(db, both, "hikvision")
    ezviz = _file(db, both, "ezviz")
    assert {item.source_code for item in both.files} == {"hikvision", "ezviz"}
    assert hikvision.sha256 == SHA_A
    assert ezviz.sha256 == SHA_B
    assert len(hikvision_only.files) == 1
    assert hikvision_only.files[0].source_code == "hikvision"
    assert ezviz_only.files[0].source_code == "ezviz"
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            _file(db, both, "hikvision", sha256="c" * 64, original_filename="second.xlsx")


def test_invalid_file_cannot_be_included_and_valid_file_can_be_excluded(db: Session) -> None:
    admin = _admin(db)
    job = _job(db, admin)
    invalid = _file(
        db,
        job,
        "hikvision",
        validation_status="invalid",
        validation_errors=["The price header is missing."],
        included_in_apply=False,
    )
    excluded = _file(
        db,
        job,
        "ezviz",
        validation_status="valid",
        validation_errors=[],
        included_in_apply=False,
    )
    assert invalid.included_in_apply is False
    assert excluded.validation_status == "valid"
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            _file(
                db,
                _job(db, admin),
                "hikvision",
                validation_status="invalid",
                validation_errors=[],
                included_in_apply=False,
            )
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            invalid.included_in_apply = True
            db.flush()


def test_conflict_stays_unapplied_until_excel_is_accepted(db: Session) -> None:
    admin = _admin(db)
    job = _job(db, admin, replace_prices=True)
    workbook = _file(db, job, "hikvision")
    product = _product(db, "hilook-e107")
    staged = ImportRow(
        import_file_id=workbook.id,
        worksheet_name="Hilook",
        source_row=107,
        classification="product",
        action="conflict",
        resolution="pending",
        raw_cells={"model": "E107", "price": "200", "note": "текущая цена со скидкой 100$"},
        proposal={
            "source_price_kind": "numeric",
            "source_price_amount": "200.00",
            "source_price_header": "Цена",
            "public_price_status": "numeric",
        },
        matched_product_id=product.id,
        messages=[
            {
                "field": "public_price_amount",
                "locked": True,
                "current": "115.00",
                "incoming": "200.00",
            }
        ],
        applied=False,
    )
    db.add(staged)
    db.flush()
    assert staged.resolution == "pending"
    assert product.price_locked is True
    assert product.stock_status == "in_stock"
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            staged.applied = True
            db.flush()
    db.expire(staged)
    staged.resolution = "accept_excel"
    staged.applied = True
    db.flush()
    db.refresh(staged)
    assert staged.applied is True
    assert staged.proposal["source_price_kind"] == "numeric"
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(
                ImportRow(
                    import_file_id=workbook.id,
                    worksheet_name="Hilook",
                    source_row=107,
                    classification="product",
                    action="unchanged",
                )
            )
            db.flush()


def test_blank_and_explicit_request_prices_remain_distinct(db: Session) -> None:
    admin = _admin(db)
    job = _job(
        db,
        admin,
        status="applied",
        approved_by=admin.id,
        applied_at=datetime.now(timezone.utc),
        summary={"inserted": 2, "blank": 1, "explicit_on_request": 1},
    )
    blank_product = Product(
        product_kind="product",
        model_raw="blank",
        model_display="blank",
        model_normalized="blank",
        public_price_status="on_request",
        slug="blank-source-price",
        catalog_status="published",
    )
    explicit_product = Product(
        product_kind="product",
        model_raw="request",
        model_display="request",
        model_normalized="request",
        public_price_status="on_request",
        slug="explicit-source-price",
        catalog_status="published",
    )
    db.add_all([blank_product, explicit_product])
    db.flush()
    blank = ProductSourceRecord(
        product_id=blank_product.id,
        source_code="hikvision",
        source_workbook="Hikvision pr.xlsx",
        source_worksheet="HDD",
        source_row=4,
        source_model_raw="blank",
        source_price_kind="blank",
        match_key="hikvision|HDD|blank",
        first_job_id=job.id,
        last_job_id=job.id,
    )
    explicit = ProductSourceRecord(
        product_id=explicit_product.id,
        source_code="hikvision",
        source_workbook="Hikvision pr.xlsx",
        source_worksheet="Проектное оборудование",
        source_row=8,
        source_model_raw="request",
        source_price_kind="explicit_on_request",
        source_price_raw="По запросу",
        source_price_header="Цена",
        match_key="hikvision|project|request",
        first_job_id=job.id,
        last_job_id=job.id,
    )
    db.add_all([blank, explicit])
    db.flush()
    assert blank.source_price_amount is None
    assert explicit.source_price_amount is None
    assert blank.source_price_kind != explicit.source_price_kind
    assert blank_product.stock_status == "in_stock"
    assert explicit_product.public_price_status == "on_request"


def test_possible_match_can_stay_separate_or_be_accepted(db: Session) -> None:
    admin = _admin(db)
    job = _job(db, admin)
    workbook = _file(db, job, "ezviz")
    existing = _product(db, "ezviz-existing")
    pending = ImportRow(
        import_file_id=workbook.id,
        worksheet_name="Ezviz",
        source_row=12,
        classification="product",
        action="possible_match",
        resolution="pending",
        matched_product_id=existing.id,
        applied=False,
    )
    separate = ImportRow(
        import_file_id=workbook.id,
        worksheet_name="Ezviz",
        source_row=13,
        classification="product",
        action="possible_match",
        resolution="accept_new",
        matched_product_id=existing.id,
        applied=False,
    )
    db.add_all([pending, separate])
    db.flush()
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            pending.applied = True
            db.flush()
    separate.applied = True
    db.flush()
    assert existing.id is not None


def test_deleting_a_preview_job_removes_staging_and_keeps_products(db: Session) -> None:
    admin = _admin(db)
    job = _job(db, admin)
    workbook = _file(db, job, "hikvision")
    product = _product(db, "kept-product")
    db.add(
        ImportRow(
            import_file_id=workbook.id,
            worksheet_name="HDD",
            source_row=2,
            classification="product",
            action="update",
            resolution="keep_current",
            matched_product_id=product.id,
        )
    )
    db.add(
        ImportAsset(
            import_file_id=workbook.id,
            object_key=f"objects/{SHA_B[:2]}/{SHA_B}.jpg",
            sha256=SHA_B,
            mime_type="image/jpeg",
            worksheet="HDD",
            anchor_row=2,
            anchor_col=2,
            proposed_product_id=product.id,
            link_status="linked_review",
        )
    )
    db.flush()
    job_id = job.id
    db.delete(job)
    db.flush()
    remaining = db.execute(
        text("SELECT count(*) FROM import_files WHERE job_id = :job_id"),
        {"job_id": job_id},
    ).scalar_one()
    assert remaining == 0
    assert db.get(Product, product.id) is not None
    assert db.get(Product, product.id).stock_status == "in_stock"


def test_applied_job_referenced_by_a_source_record_cannot_be_deleted(db: Session) -> None:
    admin = _admin(db)
    job = _job(
        db,
        admin,
        status="applied",
        approved_by=admin.id,
        applied_at=datetime.now(timezone.utc),
    )
    product = _product(db, "source-linked")
    db.add(
        ProductSourceRecord(
            product_id=product.id,
            source_code="ezviz",
            source_workbook="Ezviz pr.xlsx",
            source_worksheet="Ezviz",
            source_row=3,
            source_model_raw="CS-H8c",
            source_price_header="Цена для дилера",
            source_price_kind="numeric",
            source_price_amount=Decimal("92.50"),
            match_key="ezviz|Ezviz|cs-h8c",
            first_job_id=job.id,
            last_job_id=job.id,
        )
    )
    db.flush()
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.delete(job)
            db.flush()
    assert db.get(Product, product.id) is not None


def test_audit_actor_is_nullable_and_rejects_secret_keys(db: Session) -> None:
    admin = _admin(db)
    unknown = AdminAuditLog(
        actor_id=None,
        action="login_failure",
        detail={"email": "unknown@example.com", "result": "failure"},
        ip_address="127.0.0.1",
    )
    known = AdminAuditLog(
        actor_id=admin.id,
        action="import_apply",
        entity_type="import_job",
        entity_id=1,
        detail={"before": {"public_price_amount": "115.00"}, "after": {"public_price_amount": "200.00"}},
    )
    db.add_all([unknown, known])
    db.flush()
    assert unknown.actor_id is None
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(AdminAuditLog(action="login_failure", detail={"password": "not-stored"}))
            db.flush()
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(
                AdminAuditLog(
                    action="login_failure",
                    detail={"context": {"session_token": "not-stored"}},
                )
            )
            db.flush()


def test_upgrade_preserves_phase2a_rows_and_backfills_job_ids() -> None:
    admin_url, admin_engine = _admin_engine()
    database_url = _recreate(admin_engine, "catalog_phase2b_upgrade", admin_url)
    previous = os.environ.get("DATABASE_URL")
    config = _alembic(database_url)
    engine = create_engine(database_url)
    try:
        command.upgrade(config, "phase2a_core")
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO admin_users (email, password_hash, role)
                    VALUES ('preserved@example.com', 'stored-hash', 'admin')
                    """
                )
            )
            product_id = connection.execute(
                text(
                    """
                    INSERT INTO products (
                        product_kind, model_raw, model_display, model_normalized,
                        public_price_status, public_price_amount, public_currency,
                        price_locked, slug, catalog_status, stock_status
                    )
                    VALUES (
                        'product', 'E107', 'E107', 'e107',
                        'numeric', 200.00, 'USD',
                        true, 'preserved-e107', 'published', 'in_stock'
                    )
                    RETURNING id
                    """
                )
            ).scalar_one()
            connection.execute(
                text(
                    """
                    INSERT INTO product_translations (product_id, locale, description, origin)
                    VALUES (:product_id, 'ru', 'Сохранено', 'manual')
                    """
                ),
                {"product_id": product_id},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO product_source_records (
                        product_id, source_code, source_workbook, source_worksheet, source_row,
                        source_model_raw, source_price_kind, source_price_amount, source_price_header,
                        internal_note, match_key, first_job_id, last_job_id
                    )
                    VALUES (
                        :product_id, 'hikvision', 'Hikvision pr.xlsx', 'Hilook', 107,
                        'E107', 'numeric', 200.00, 'Цена',
                        'текущая цена со скидкой 100$', 'hikvision|Hilook|e107', 7, 9
                    )
                    """
                ),
                {"product_id": product_id},
            )
        command.upgrade(config, "head")
        with engine.connect() as connection:
            product = connection.execute(
                text(
                    """
                    SELECT slug, public_price_amount, price_locked, stock_status, catalog_status
                    FROM products WHERE id = :product_id
                    """
                ),
                {"product_id": product_id},
            ).one()
            source = connection.execute(
                text(
                    """
                    SELECT source_price_kind, source_price_amount, internal_note,
                           first_job_id, last_job_id, absent_from_latest
                    FROM product_source_records WHERE product_id = :product_id
                    """
                ),
                {"product_id": product_id},
            ).one()
            description = connection.execute(
                text(
                    """
                    SELECT description, origin FROM product_translations
                    WHERE product_id = :product_id AND locale = 'ru'
                    """
                ),
                {"product_id": product_id},
            ).one()
            profile_count = connection.execute(text("SELECT count(*) FROM business_profile")).scalar_one()
            jobs = connection.execute(
                text(
                    """
                    SELECT id, status, publish_new_products, replace_prices, summary->>'origin'
                    FROM import_jobs ORDER BY id
                    """
                )
            ).all()
            validated = connection.execute(
                text(
                    """
                    SELECT conname, convalidated
                    FROM pg_constraint
                    WHERE conname IN (
                        'fk_product_source_records_first_job_id',
                        'fk_product_source_records_last_job_id'
                    )
                    ORDER BY conname
                    """
                )
            ).all()
            version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert product.slug == "preserved-e107"
        assert product.public_price_amount == 200
        assert product.price_locked is True
        assert product.stock_status == "in_stock"
        assert product.catalog_status == "published"
        assert source.source_price_kind == "numeric"
        assert source.internal_note == "текущая цена со скидкой 100$"
        assert source.first_job_id == 7
        assert source.last_job_id == 9
        assert source.absent_from_latest is False
        assert description.description == "Сохранено"
        assert description.origin == "manual"
        assert profile_count == 1
        assert [(row.id, row.status) for row in jobs] == [(7, "applied"), (9, "applied")]
        assert all(row.publish_new_products is True and row.replace_prices is False for row in jobs)
        assert all(row[4] == "phase2b_foreign_key_backfill" for row in jobs)
        assert validated == [
            ("fk_product_source_records_first_job_id", True),
            ("fk_product_source_records_last_job_id", True),
        ]
        assert version == "phase3_admin_sessions"
        command.downgrade(config, "phase2a_core")
        with engine.connect() as connection:
            names = {
                row[0]
                for row in connection.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                )
            }
            surviving = connection.execute(
                text("SELECT slug, stock_status FROM products WHERE id = :product_id"),
                {"product_id": product_id},
            ).one()
            downgraded = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert "import_jobs" not in names
        assert "products" in names
        assert surviving.slug == "preserved-e107"
        assert surviving.stock_status == "in_stock"
        assert downgraded == "phase2a_core"
    finally:
        engine.dispose()
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()
        with admin_engine.connect() as connection:
            connection.execute(text('DROP DATABASE IF EXISTS "catalog_phase2b_upgrade" WITH (FORCE)'))
        admin_engine.dispose()


def test_upgrade_without_an_admin_keeps_orphan_source_rows() -> None:
    admin_url, admin_engine = _admin_engine()
    database_url = _recreate(admin_engine, "catalog_phase2b_orphan", admin_url)
    previous = os.environ.get("DATABASE_URL")
    config = _alembic(database_url)
    engine = create_engine(database_url)
    try:
        command.upgrade(config, "phase2a_core")
        with engine.begin() as connection:
            product_id = connection.execute(
                text(
                    """
                    INSERT INTO products (
                        product_kind, model_raw, model_display, model_normalized,
                        public_price_status, slug, catalog_status
                    )
                    VALUES ('product', 'orphan', 'orphan', 'orphan', 'on_request', 'orphan-product', 'draft')
                    RETURNING id
                    """
                )
            ).scalar_one()
            connection.execute(
                text(
                    """
                    INSERT INTO product_source_records (
                        product_id, source_code, source_workbook, source_worksheet, source_row,
                        source_model_raw, source_price_kind, match_key, first_job_id, last_job_id
                    )
                    VALUES (
                        :product_id, 'ezviz', 'Ezviz pr.xlsx', 'Ezviz', 2,
                        'orphan', 'blank', 'ezviz|Ezviz|orphan', 3, 3
                    )
                    """
                ),
                {"product_id": product_id},
            )
        command.upgrade(config, "head")
        with engine.connect() as connection:
            source = connection.execute(
                text(
                    """
                    SELECT source_price_kind, first_job_id
                    FROM product_source_records WHERE product_id = :product_id
                    """
                ),
                {"product_id": product_id},
            ).one()
            job_count = connection.execute(text("SELECT count(*) FROM import_jobs")).scalar_one()
            validated = connection.execute(
                text(
                    """
                    SELECT bool_and(convalidated)
                    FROM pg_constraint
                    WHERE conname IN (
                        'fk_product_source_records_first_job_id',
                        'fk_product_source_records_last_job_id'
                    )
                    """
                )
            ).scalar_one()
        assert source.source_price_kind == "blank"
        assert source.first_job_id == 3
        assert job_count == 0
        assert validated is False
    finally:
        engine.dispose()
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()
        with admin_engine.connect() as connection:
            connection.execute(text('DROP DATABASE IF EXISTS "catalog_phase2b_orphan" WITH (FORCE)'))
        admin_engine.dispose()
