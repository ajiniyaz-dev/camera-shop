"""Approved UZ/EN product-name data patch."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.data.approved_uz_en_product_names import (
    APPROVED_UZ_EN_PRODUCT_NAMES,
    EXPECTED_PRODUCT_IDS,
    SKIPPED_UNRESOLVED_PRODUCT_IDS,
    apply_approved_uz_en_product_names,
    iter_approved_name_rows,
    revert_approved_uz_en_product_names,
)
from app.models import Product, ProductTranslation

API_ROOT = Path(__file__).resolve().parents[1]

# Exact high-confidence set from docs/translation-approval-list.md (excluding review IDs).
APPROVAL_LIST_HIGH_IDS = {
    444,
    445,
    462,
    463,
    464,
    468,
    477,
    478,
    479,
    480,
    511,
    513,
    514,
    638,
    639,
    640,
    641,
}

APPROVAL_LIST_NAMES = {
    444: ("T311 tripod turniket", "T311 tripod turnstile"),
    445: ("T315 portal turniket", "T315 portal turnstile"),
    462: ("180 kg elektromagnit qulf", "180 kg electromagnetic lock"),
    463: ("280 kg elektromagnit qulf", "280 kg electromagnetic lock"),
    464: ("350 kg elektromagnit qulf", "350 kg electromagnetic lock"),
    468: ("Kontaktsiz EM-Marine karta", "Contactless EM-Marine card"),
    477: ("Kronshteyn 20SM M-611", "Bracket 20SM M-611"),
    478: ("Kronshteyn 30SMX60SM M-901", "Bracket 30SMX60SM M-901"),
    479: ("Kronshteyn 30SM M-612", "Bracket 30SM M-612"),
    480: ("Kronshteyn 60SMX120SM M-901", "Bracket 60SMX120SM M-901"),
    511: ("Rozetkalar bloki", "Socket block"),
    513: ("Patch panel", "Patch panel"),
    514: ("Kabel organayzeri", "Cable organizer"),
    638: ("7 kunlik voqealar videotarixi", "7-day video event history"),
    639: ("30 kunlik voqealar videotarixi", "30-day video event history"),
    640: ("7 kunlik voqealar videotarixi", "7-day video event history"),
    641: ("30 kunlik voqealar videotarixi", "30-day video event history"),
}

ADMIN_URLS = [
    os.environ.get("PHASE2A_ADMIN_URL"),
    "postgresql+psycopg://catalog:change-me@127.0.0.1:5433/postgres",
    "postgresql+psycopg://catalog:catalog@127.0.0.1:5432/postgres",
]


def test_approved_set_matches_translation_approval_list() -> None:
    assert set(EXPECTED_PRODUCT_IDS.values()) == APPROVAL_LIST_HIGH_IDS
    assert len(APPROVED_UZ_EN_PRODUCT_NAMES) == 17
    assert len(iter_approved_name_rows()) == 34
    assert SKIPPED_UNRESOLVED_PRODUCT_IDS.isdisjoint(APPROVAL_LIST_HIGH_IDS)
    for slug, product_id in EXPECTED_PRODUCT_IDS.items():
        uz, en = APPROVAL_LIST_NAMES[product_id]
        assert APPROVED_UZ_EN_PRODUCT_NAMES[slug]["uz"] == uz
        assert APPROVED_UZ_EN_PRODUCT_NAMES[slug]["en"] == en


def test_approved_names_cover_only_uz_and_en() -> None:
    for names in APPROVED_UZ_EN_PRODUCT_NAMES.values():
        assert set(names) == {"uz", "en"}
        assert names["uz"].strip()
        assert names["en"].strip()


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
def names_engine():
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
        pytest.skip("PostgreSQL is not reachable for disposable approved-names tests")

    name = "catalog_approved_names_test"
    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    database_url = admin_url.rsplit("/", 1)[0] + "/" + name
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    try:
        command.upgrade(config, "head")
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
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin_engine.dispose()


def _add_product(db: Session, slug: str, *, uz_name: str | None, en_name: str | None) -> int:
    product = Product(
        slug=slug,
        model_display=slug,
        model_raw=slug,
        model_normalized=slug,
        catalog_status="published",
        stock_status="in_stock",
        public_price_status="on_request",
        product_kind="product",
    )
    db.add(product)
    db.flush()
    db.add_all(
        [
            ProductTranslation(
                product_id=product.id,
                locale="ru",
                localized_name="RU name",
                description="ru-desc",
                origin="manual",
            ),
            ProductTranslation(
                product_id=product.id,
                locale="uz",
                localized_name=uz_name,
                description="uz-desc",
                origin="manual",
            ),
            ProductTranslation(
                product_id=product.id,
                locale="en",
                localized_name=en_name,
                description="en-desc",
                origin="manual",
            ),
        ]
    )
    db.commit()
    return product.id


def test_apply_sets_blank_names_and_preserves_descriptions(names_engine) -> None:
    with Session(bind=names_engine) as db:
        product_id = _add_product(db, "product-turniket-t311", uz_name=None, en_name=None)

    with names_engine.begin() as connection:
        first = apply_approved_uz_en_product_names(connection)
        second = apply_approved_uz_en_product_names(connection)
    assert first == 2
    assert second == 2

    with names_engine.connect() as connection:
        rows = {
            row["locale"]: row
            for row in connection.execute(
                text(
                    """
                    SELECT locale, localized_name, description
                    FROM product_translations
                    WHERE product_id = :pid
                    """
                ),
                {"pid": product_id},
            ).mappings()
        }
    assert rows["ru"]["localized_name"] == "RU name"
    assert rows["uz"]["localized_name"] == "T311 tripod turniket"
    assert rows["en"]["localized_name"] == "T311 tripod turnstile"
    assert rows["uz"]["description"] == "uz-desc"
    assert rows["en"]["description"] == "en-desc"


def test_apply_does_not_overwrite_divergent_admin_name(names_engine) -> None:
    with Session(bind=names_engine) as db:
        product_id = _add_product(
            db,
            "product-blok-rozetok",
            uz_name="Custom admin UZ title",
            en_name=None,
        )

    with names_engine.begin() as connection:
        updated = apply_approved_uz_en_product_names(connection)
    assert updated >= 1

    with names_engine.connect() as connection:
        rows = {
            row["locale"]: row["localized_name"]
            for row in connection.execute(
                text(
                    """
                    SELECT locale, localized_name
                    FROM product_translations
                    WHERE product_id = :pid
                    """
                ),
                {"pid": product_id},
            ).mappings()
        }
    assert rows["uz"] == "Custom admin UZ title"
    assert rows["en"] == "Socket block"


def test_revert_clears_only_matching_approved_names(names_engine) -> None:
    with Session(bind=names_engine) as db:
        product_id = _add_product(
            db,
            "product-patch-panel",
            uz_name="Patch panel",
            en_name="Patch panel",
        )

    with names_engine.begin() as connection:
        cleared = revert_approved_uz_en_product_names(connection)
    assert cleared >= 2

    with names_engine.connect() as connection:
        rows = {
            row["locale"]: row["localized_name"]
            for row in connection.execute(
                text(
                    """
                    SELECT locale, localized_name
                    FROM product_translations
                    WHERE product_id = :pid
                    """
                ),
                {"pid": product_id},
            ).mappings()
        }
    assert rows["ru"] == "RU name"
    assert rows["uz"] is None
    assert rows["en"] is None


def test_migration_head_applies_approved_names(names_engine) -> None:
    with names_engine.connect() as connection:
        version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert version == "source_backed_missing_primaries"
