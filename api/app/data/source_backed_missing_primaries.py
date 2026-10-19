"""Link six published products to their verified workbook photo-column images.

Each product already has a ``linked_high`` ``import_assets`` row on its exact
source worksheet/row (Job 5). The catalog image rows were never created.
Checksums may also appear on a neighboring model row; the client allows that
reuse. Match by stable product slug. Do not invent associations.

Manual protection: skip any product that already has a non-rejected
``product_images`` row. Idempotent: a second apply is a no-op when the
approved checksum is already attached.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from sqlalchemy import Connection, text

from app.importing.images import SOURCE_PUBLISHABLE_LINK_STATUSES

# slug -> verified association (documentation ids are not used for matching)
SOURCE_BACKED_MISSING_PRIMARIES: dict[str, dict[str, object]] = {
    "hilook-ipc-b160ha-luf-sl": {
        "expected_product_id": 37,
        "source_code": "hikvision",
        "source_worksheet": "Hilook",
        "anchor_row": 22,
        "anchor_col": 2,
        "anchor_to_row": 23,
        "sha256": "fa83f324b1c9b4a26ea58181f06595c339dfc71a74e8cdc87f08a0668666afad",
        "object_key": "objects/fa/fa83f324b1c9b4a26ea58181f06595c339dfc71a74e8cdc87f08a0668666afad.png",
        "mime_type": "image/png",
        "alt_text": "IPC-B160HA-LUF/SL",
    },
    "hilook-ds-kis202t": {
        "expected_product_id": 110,
        "source_code": "hikvision",
        "source_worksheet": "Hilook",
        "anchor_row": 121,
        "anchor_col": 2,
        "anchor_to_row": 121,
        "sha256": "7ca0d55905dc5af2c347d9ea6034fb7c56afbf05830941177dff7c80fc372490",
        "object_key": "objects/7c/7ca0d55905dc5af2c347d9ea6034fb7c56afbf05830941177dff7c80fc372490.png",
        "mime_type": "image/png",
        "alt_text": "DS-KIS202T",
    },
    "hilook-vdp-k203": {
        "expected_product_id": 111,
        "source_code": "hikvision",
        "source_worksheet": "Hilook",
        "anchor_row": 122,
        "anchor_col": 2,
        "anchor_to_row": 122,
        "sha256": "7ca0d55905dc5af2c347d9ea6034fb7c56afbf05830941177dff7c80fc372490",
        "object_key": "objects/7c/7ca0d55905dc5af2c347d9ea6034fb7c56afbf05830941177dff7c80fc372490.png",
        "mime_type": "image/png",
        "alt_text": "VDP-K203",
    },
    "hikvision-ds-2cd2t83g2-4li2u-4mm-black": {
        "expected_product_id": 184,
        "source_code": "hikvision",
        "source_worksheet": "IP камеры",
        "anchor_row": 63,
        "anchor_col": 2,
        "anchor_to_row": 63,
        "sha256": "d07ed6cc9d18a0864844d4897fa7a638915f1b965f7616c205515b4fea5bd357",
        "object_key": "objects/d0/d07ed6cc9d18a0864844d4897fa7a638915f1b965f7616c205515b4fea5bd357.png",
        "mime_type": "image/png",
        "alt_text": "DS-2CD2T83G2-4LI2U 4MM Black",
    },
    "hikvision-ds-2cd2687g3-lizs2uy-sl": {
        "expected_product_id": 200,
        "source_code": "hikvision",
        "source_worksheet": "IP камеры",
        "anchor_row": 79,
        "anchor_col": 2,
        "anchor_to_row": 79,
        "sha256": "32a855e5fdf8f2586976a7c6b3dda21af39057277febc5035ebea5e94e830fb2",
        "object_key": "objects/32/32a855e5fdf8f2586976a7c6b3dda21af39057277febc5035ebea5e94e830fb2.png",
        "mime_type": "image/png",
        "alt_text": "DS-2CD2687G3-LIZS2UY/SL",
    },
    "hikvision-ids-tcm403-b": {
        "expected_product_id": 383,
        "source_code": "hikvision",
        "source_worksheet": "Проектное оборудование",
        "anchor_row": 15,
        "anchor_col": 2,
        "anchor_to_row": 15,
        "sha256": "22d751c6e19d54a20083b6f4c6301406d1a8a54a8c54f1c9de10f3fdb994f488",
        "object_key": "objects/22/22d751c6e19d54a20083b6f4c6301406d1a8a54a8c54f1c9de10f3fdb994f488.png",
        "mime_type": "image/png",
        "alt_text": "IDS-TCM403-B",
    },
}

EXPECTED_PRODUCT_IDS: dict[str, int] = {
    slug: int(spec["expected_product_id"]) for slug, spec in SOURCE_BACKED_MISSING_PRIMARIES.items()
}


def apply_source_backed_missing_primaries(
    connection: Connection,
    *,
    media_root: Path | None = None,
    specs: Mapping[str, Mapping[str, object]] = SOURCE_BACKED_MISSING_PRIMARIES,
) -> int:
    """Attach verified photo-column images when the product still has none.

    Requires a publishable ``import_assets`` row on the product's source
    worksheet/row with the approved checksum. When ``media_root`` is set, the
    object file must exist. Returns the number of ``product_images`` rows inserted.
    """

    inserted = 0
    for slug in sorted(specs):
        spec = specs[slug]
        product = connection.execute(
            text(
                """
                SELECT id
                FROM products
                WHERE slug = :slug AND deleted_at IS NULL
                """
            ),
            {"slug": slug},
        ).mappings().one_or_none()
        if product is None:
            continue
        product_id = int(product["id"])
        existing = connection.execute(
            text(
                """
                SELECT count(*) FROM product_images
                WHERE product_id = :pid AND association_status <> 'rejected'
                """
            ),
            {"pid": product_id},
        ).scalar_one()
        if existing:
            continue
        assert SOURCE_PUBLISHABLE_LINK_STATUSES == frozenset({"linked_high", "shared_candidate"})
        asset = connection.execute(
            text(
                """
                SELECT a.object_key, a.mime_type, a.sha256, a.anchor_row, a.anchor_col, a.anchor_to_row
                FROM product_source_records AS psr
                JOIN import_assets AS a
                  ON a.worksheet = psr.source_worksheet
                 AND a.anchor_row = psr.source_row
                 AND a.link_status IN ('linked_high', 'shared_candidate')
                 AND a.sha256 = :sha256
                WHERE psr.product_id = :pid
                  AND psr.source_worksheet = :worksheet
                  AND psr.source_row = :anchor_row
                ORDER BY a.id DESC
                LIMIT 1
                """
            ),
            {
                "pid": product_id,
                "worksheet": spec["source_worksheet"],
                "anchor_row": spec["anchor_row"],
                "sha256": spec["sha256"],
            },
        ).mappings().one_or_none()
        if asset is None:
            continue
        object_key = str(asset["object_key"])
        if media_root is None:
            raise ValueError("media_root is required so byte_size comes from the stored object")
        path = (media_root / object_key).resolve()
        if media_root.resolve() not in path.parents or not path.is_file():
            continue
        byte_size = path.stat().st_size
        connection.execute(
            text(
                """
                INSERT INTO product_images (
                    product_id, storage_backend, object_key, mime_type, byte_size, sha256,
                    sort_order, is_primary, alt_text, association_status, source_code,
                    source_worksheet, anchor_row, anchor_col, anchor_to_row
                ) VALUES (
                    :product_id, 'local', :object_key, :mime_type, :byte_size, :sha256,
                    0, true, :alt_text, 'high', :source_code,
                    :source_worksheet, :anchor_row, :anchor_col, :anchor_to_row
                )
                """
            ),
            {
                "product_id": product_id,
                "object_key": object_key,
                "mime_type": asset["mime_type"] or spec["mime_type"],
                "byte_size": byte_size,
                "sha256": asset["sha256"],
                "alt_text": spec["alt_text"],
                "source_code": spec["source_code"],
                "source_worksheet": spec["source_worksheet"],
                "anchor_row": asset["anchor_row"],
                "anchor_col": asset["anchor_col"],
                "anchor_to_row": asset["anchor_to_row"],
            },
        )
        inserted += 1
    return inserted


def revert_source_backed_missing_primaries(
    connection: Connection,
    *,
    specs: Mapping[str, Mapping[str, object]] = SOURCE_BACKED_MISSING_PRIMARIES,
) -> int:
    """Remove only high-confidence rows that still match this patch's checksum and anchors."""

    cleared = 0
    for slug in sorted(specs):
        spec = specs[slug]
        result = connection.execute(
            text(
                """
                DELETE FROM product_images AS i
                USING products AS p
                WHERE p.id = i.product_id
                  AND p.slug = :slug
                  AND i.sha256 = :sha256
                  AND i.association_status = 'high'
                  AND i.anchor_row = :anchor_row
                  AND i.source_worksheet = :worksheet
                """
            ),
            {
                "slug": slug,
                "sha256": spec["sha256"],
                "anchor_row": spec["anchor_row"],
                "worksheet": spec["source_worksheet"],
            },
        )
        cleared += result.rowcount or 0
    return cleared
