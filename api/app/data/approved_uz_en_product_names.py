"""Approved Uzbek/English product ``localized_name`` values (Oct 2026).

Source of truth for wording: ``docs/translation-approval-list.md`` (high-confidence
rows only). Keys are stable product slugs. Numeric product ids are recorded for
documentation and verification against the local Compose catalog; apply/revert
always match by slug so a rebuilt database with different ids still works.

Unresolved / medium-confidence products are intentionally omitted:
25, 469, 512, 515, 621, 636, 637.
"""

from __future__ import annotations

from typing import Mapping

from sqlalchemy import Connection, text

# slug -> {locale: localized_name}
APPROVED_UZ_EN_PRODUCT_NAMES: dict[str, dict[str, str]] = {
    "product-turniket-t311": {
        "uz": "T311 tripod turniket",
        "en": "T311 tripod turnstile",
    },
    "product-turniket-t315": {
        "uz": "T315 portal turniket",
        "en": "T315 portal turnstile",
    },
    "product-zamok-180kg": {
        "uz": "180 kg elektromagnit qulf",
        "en": "180 kg electromagnetic lock",
    },
    "product-zamok-280kg": {
        "uz": "280 kg elektromagnit qulf",
        "en": "280 kg electromagnetic lock",
    },
    "product-zamok-350kg": {
        "uz": "350 kg elektromagnit qulf",
        "en": "350 kg electromagnetic lock",
    },
    "product-karta-em-marine": {
        "uz": "Kontaktsiz EM-Marine karta",
        "en": "Contactless EM-Marine card",
    },
    "product-kronshteyn-20sm-m-611": {
        "uz": "Kronshteyn 20SM M-611",
        "en": "Bracket 20SM M-611",
    },
    "product-kronshteyn-30smx60sm-m-901": {
        "uz": "Kronshteyn 30SMX60SM M-901",
        "en": "Bracket 30SMX60SM M-901",
    },
    "product-kronshteyn-30sm-m-612": {
        "uz": "Kronshteyn 30SM M-612",
        "en": "Bracket 30SM M-612",
    },
    "product-kronshteyn-60smx120sm-m-901": {
        "uz": "Kronshteyn 60SMX120SM M-901",
        "en": "Bracket 60SMX120SM M-901",
    },
    "product-blok-rozetok": {
        "uz": "Rozetkalar bloki",
        "en": "Socket block",
    },
    "product-patch-panel": {
        "uz": "Patch panel",
        "en": "Patch panel",
    },
    "product-organayzer": {
        "uz": "Kabel organayzeri",
        "en": "Cable organizer",
    },
    "ezviz-7-dnevnaya-videoistoriya-sobytiy-ezhemesyachno": {
        "uz": "7 kunlik voqealar videotarixi",
        "en": "7-day video event history",
    },
    "ezviz-30-dnevnaya-videoistoriya-sobytiy-ezhemesyachno": {
        "uz": "30 kunlik voqealar videotarixi",
        "en": "30-day video event history",
    },
    "ezviz-7-dnevnaya-videoistoriya-sobytiy-ezhegodno": {
        "uz": "7 kunlik voqealar videotarixi",
        "en": "7-day video event history",
    },
    "ezviz-30-dnevnaya-videoistoriya-sobytiy-ezhegodno": {
        "uz": "30 kunlik voqealar videotarixi",
        "en": "30-day video event history",
    },
}

# Local Compose catalog ids when the approved names were applied (documentation only).
EXPECTED_PRODUCT_IDS: dict[str, int] = {
    "product-turniket-t311": 444,
    "product-turniket-t315": 445,
    "product-zamok-180kg": 462,
    "product-zamok-280kg": 463,
    "product-zamok-350kg": 464,
    "product-karta-em-marine": 468,
    "product-kronshteyn-20sm-m-611": 477,
    "product-kronshteyn-30smx60sm-m-901": 478,
    "product-kronshteyn-30sm-m-612": 479,
    "product-kronshteyn-60smx120sm-m-901": 480,
    "product-blok-rozetok": 511,
    "product-patch-panel": 513,
    "product-organayzer": 514,
    "ezviz-7-dnevnaya-videoistoriya-sobytiy-ezhemesyachno": 638,
    "ezviz-30-dnevnaya-videoistoriya-sobytiy-ezhemesyachno": 639,
    "ezviz-7-dnevnaya-videoistoriya-sobytiy-ezhegodno": 640,
    "ezviz-30-dnevnaya-videoistoriya-sobytiy-ezhegodno": 641,
}

SKIPPED_UNRESOLVED_PRODUCT_IDS: frozenset[int] = frozenset({25, 469, 512, 515, 621, 636, 637})


def iter_approved_name_rows(
    names: Mapping[str, Mapping[str, str]] = APPROVED_UZ_EN_PRODUCT_NAMES,
) -> list[tuple[str, str, str]]:
    """Return ``(slug, locale, localized_name)`` rows in stable order."""
    rows: list[tuple[str, str, str]] = []
    for slug in sorted(names):
        for locale in ("uz", "en"):
            rows.append((slug, locale, names[slug][locale]))
    return rows


def apply_approved_uz_en_product_names(connection: Connection) -> int:
    """Set approved UZ/EN names when blank or already equal to the approved value.

    Skips rows whose ``localized_name`` is a different non-null value so later
    admin edits are not overwritten. Does not touch descriptions, Russian names,
    models, prices, or other locales. Returns the number of rows updated.
    """
    updated = 0
    for slug, locale, name in iter_approved_name_rows():
        result = connection.execute(
            text(
                """
                UPDATE product_translations AS t
                SET localized_name = :name
                FROM products AS p
                WHERE p.id = t.product_id
                  AND p.slug = :slug
                  AND t.locale = :locale
                  AND (t.localized_name IS NULL OR t.localized_name = :name)
                """
            ),
            {"slug": slug, "locale": locale, "name": name},
        )
        updated += result.rowcount or 0
    return updated


def revert_approved_uz_en_product_names(connection: Connection) -> int:
    """Clear approved names only when the current value still matches the approved text."""
    cleared = 0
    for slug, locale, name in iter_approved_name_rows():
        result = connection.execute(
            text(
                """
                UPDATE product_translations AS t
                SET localized_name = NULL
                FROM products AS p
                WHERE p.id = t.product_id
                  AND p.slug = :slug
                  AND t.locale = :locale
                  AND t.localized_name = :name
                """
            ),
            {"slug": slug, "locale": locale, "name": name},
        )
        cleared += result.rowcount or 0
    return cleared
