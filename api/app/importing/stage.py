"""Stage parsed workbooks onto an existing preview job. Live products are not updated."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.importing.images import object_key
from app.importing.match import ExistingSource, match_rows
from app.importing.parse import (
    ParsedRow,
    ParsedWorkbook,
    inspect_container,
    read_workbook,
)
from app.models import (
    Brand,
    Category,
    ImportAsset,
    ImportFile,
    ImportJob,
    ImportRow,
    Product,
    ProductSourceRecord,
)

class StagingError(Exception):
    """The job cannot be staged. The caller should roll the database transaction back."""


@dataclass(frozen=True)
class SourceInput:
    path: Path
    original_filename: str
    identification: str = "auto"
    declared_source: str | None = None


def stage_import(
    session: Session,
    job: ImportJob,
    sources: list[SourceInput],
    media_root: Path,
) -> dict[str, Any]:
    """Parse and stage one or both workbooks. The caller commits. This function only flushes."""

    if job.id is None:
        raise StagingError("The import job must be saved before staging.")
    if job.status != "preview":
        raise StagingError("Only a preview job can be staged.")
    root = _assert_media_root(media_root)
    prepared, rejected = _prepare(sources)
    partials: list[Path] = []
    workbook_copies: list[Path] = []
    try:
        stored_keys = [_store_images(root, item["parsed"], partials) for item in prepared]
        workbook_partials = []
        for item in prepared:
            partial = _workbook_partial(root, job.id, item["source_code"], item["content"])
            partials.append(partial)
            workbook_partials.append(partial)
        summary = _persist(session, job, prepared, rejected, stored_keys)
        session.flush()
        for partial, item in zip(workbook_partials, prepared, strict=True):
            final = _safe_path(root, f"imports/{job.id}/{item['source_code']}.xlsx")
            final.parent.mkdir(parents=True, exist_ok=True)
            partial.replace(final)
            partials.remove(partial)
            workbook_copies.append(final)
        return summary
    except Exception:
        for partial in partials:
            partial.unlink(missing_ok=True)
        for copy in workbook_copies:
            copy.unlink(missing_ok=True)
        raise


def _prepare(sources: list[SourceInput]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    prepared: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in sources:
        if source.identification not in {"auto", "admin_confirmed"}:
            raise StagingError("Identification must be auto or admin_confirmed.")
        inspection = inspect_container(source.path, source.original_filename)
        resolved = _resolve(source, inspection)
        rejection = _rejection(source, inspection, resolved)
        if rejection is not None:
            rejected.append(rejection)
            continue
        assert resolved is not None
        if resolved in seen:
            raise StagingError("A job can contain only one file for each source.")
        seen.add(resolved)
        parsed = read_workbook(source.path, resolved)
        if not parsed.has_required_sheet:
            rejected.append(
                {
                    "original_filename": _basename(source.original_filename),
                    "sha256": _file_sha256(source.path),
                    "code": "missing_required_header",
                    "signature": inspection.signature,
                    "filename_hint": inspection.filename_hint,
                    "errors": parsed.errors,
                }
            )
            continue
        prepared.append(
            {
                "source_code": resolved,
                "input": source,
                "parsed": parsed,
                "content": source.path.read_bytes(),
                "sha256": _file_sha256(source.path),
                "filename": _basename(source.original_filename),
            }
        )
    return prepared, rejected


def _resolve(source: SourceInput, inspection: Any) -> str | None:
    if inspection.container_errors or len(inspection.signatures) > 1:
        return None
    if source.identification == "admin_confirmed":
        if source.declared_source not in {"hikvision", "ezviz"}:
            return None
        if not any(item["signature"] == source.declared_source for item in inspection.sheet_headers):
            return None
        return source.declared_source
    if inspection.signature is None:
        return None
    if inspection.filename_hint is not None and inspection.filename_hint != inspection.signature:
        return None
    return inspection.signature


def _rejection(source: SourceInput, inspection: Any, resolved: str | None) -> dict[str, Any] | None:
    if resolved is not None:
        return None
    code = "unidentified_workbook"
    if inspection.container_errors:
        code = str(inspection.container_errors[0]["code"])
    elif len(inspection.signatures) > 1:
        code = "ambiguous_signature"
    elif source.identification == "admin_confirmed":
        code = "confirmed_source_missing_columns"
    elif inspection.filename_hint and inspection.signature and inspection.filename_hint != inspection.signature:
        code = "filename_signature_disagreement"
    sha = None
    if source.path.is_file():
        try:
            sha = _file_sha256(source.path)
        except OSError:
            sha = None
    return {
        "original_filename": _basename(source.original_filename),
        "sha256": sha,
        "code": code,
        "signature": inspection.signature,
        "filename_hint": inspection.filename_hint,
        "errors": list(inspection.container_errors),
    }


def _persist(
    session: Session,
    job: ImportJob,
    prepared: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    stored_keys: list[dict[str, str]],
) -> dict[str, Any]:
    source_summaries: list[dict[str, Any]] = []
    for item, keys in zip(prepared, stored_keys, strict=True):
        parsed: ParsedWorkbook = item["parsed"]
        existing_records = _load_existing(session, item["source_code"])
        rows = [row for sheet in parsed.sheets for row in sheet.rows]
        absent = match_rows(rows, existing_records, replace_prices=bool(job.replace_prices))
        record = _upsert_file(session, job, item, parsed)
        _replace_children(session, record.id)
        for row in rows:
            session.add(_import_row(record.id, row))
        for sheet in parsed.sheets:
            for image in sheet.images:
                if image.rejected or image.mime_type is None or image.extension is None:
                    continue
                matched = _matched_product(rows, image.worksheet, image.row)
                session.add(
                    ImportAsset(
                        import_file_id=record.id,
                        object_key=keys[image.sha256],
                        sha256=image.sha256,
                        mime_type=image.mime_type,
                        worksheet=image.worksheet,
                        anchor_row=image.row,
                        anchor_col=image.col,
                        anchor_to_row=image.to_row,
                        proposed_product_id=matched,
                        link_status=image.link_status or "unassigned",
                    )
                )
        source_summaries.append(_source_summary(item, parsed, rows, absent))
    summary = {
        "sources": source_summaries,
        "rejected_files": rejected,
        "combined": _combine(source_summaries),
    }
    job.summary = summary
    job.status = "preview"
    job.error_message = None
    return summary


def _upsert_file(session: Session, job: ImportJob, item: dict[str, Any], parsed: ParsedWorkbook) -> ImportFile:
    errors = [*parsed.errors, *parsed.warnings]
    for sheet in parsed.sheets:
        errors.extend(sheet.errors)
        errors.extend(sheet.warnings)
    record = session.scalars(
        select(ImportFile).where(
            ImportFile.job_id == job.id,
            ImportFile.source_code == item["source_code"],
        )
    ).one_or_none()
    identification = item["input"].identification
    if record is None:
        record = ImportFile(
            job_id=job.id,
            source_code=item["source_code"],
            original_filename=item["filename"],
            sha256=item["sha256"],
            identification=identification,
            validation_status="valid",
            validation_errors=errors,
            stored_object_key=f"imports/{job.id}/{item['source_code']}.xlsx",
            included_in_apply=True,
        )
        session.add(record)
    else:
        record.original_filename = item["filename"]
        record.sha256 = item["sha256"]
        record.identification = identification
        record.validation_status = "valid"
        record.validation_errors = errors
        record.stored_object_key = f"imports/{job.id}/{item['source_code']}.xlsx"
        record.included_in_apply = True
    session.flush()
    return record


def _replace_children(session: Session, import_file_id: int) -> None:
    session.execute(delete(ImportRow).where(ImportRow.import_file_id == import_file_id))
    session.execute(delete(ImportAsset).where(ImportAsset.import_file_id == import_file_id))


def _import_row(import_file_id: int, row: ParsedRow) -> ImportRow:
    return ImportRow(
        import_file_id=import_file_id,
        worksheet_name=row.worksheet_name,
        source_row=row.source_row,
        classification=row.classification,
        action=row.action,
        resolution=row.resolution,
        raw_cells=row.raw_cells,
        proposal=row.proposal,
        matched_product_id=row.matched_product_id,
        messages=row.messages,
        applied=False,
    )


def _load_existing(session: Session, source_code: str) -> list[ExistingSource]:
    records = session.scalars(
        select(ProductSourceRecord)
        .where(ProductSourceRecord.source_code == source_code)
        .options(
            selectinload(ProductSourceRecord.product).selectinload(Product.translations),
            selectinload(ProductSourceRecord.product)
            .selectinload(Product.brand)
            .selectinload(Brand.translations),
            selectinload(ProductSourceRecord.product)
            .selectinload(Product.category)
            .selectinload(Category.translations),
        )
    ).all()
    loaded: list[ExistingSource] = []
    for record in records:
        product = record.product
        loaded.append(
            ExistingSource(
                product_id=product.id,
                match_key=record.match_key,
                worksheet=record.source_worksheet,
                model_normalized=product.model_normalized,
                option_label=product.option_label,
                model_display=product.model_display,
                description=_ru_description(product),
                public_price_status=product.public_price_status,
                public_price_amount=product.public_price_amount,
                public_currency=product.public_currency,
                source_price_kind=record.source_price_kind,
                brand_name=_ru_name(product.brand.translations) if product.brand is not None else None,
                category_name=(
                    _ru_name(product.category.translations) if product.category is not None else None
                ),
                price_locked=product.price_locked,
                option_locked=product.option_locked,
                brand_locked=product.brand_locked,
                category_locked=product.category_locked,
                model_locked=product.model_locked,
                description_locked=_description_locked(product),
            )
        )
    return loaded


def _store_images(root: Path, parsed: ParsedWorkbook, partials: list[Path]) -> dict[str, str]:
    """Write new checksum objects. A failed attempt does not delete them.

    The same hash can already belong to another job or product, including one
    that has not committed yet. Unreferenced objects are left for a later
    cleanup that checks ``product_images`` and ``import_assets``.
    """

    keys: dict[str, str] = {}
    for sheet in parsed.sheets:
        for image in sheet.images:
            if image.rejected or image.extension is None or not image.sha256:
                continue
            key = object_key(image.sha256, image.extension)
            keys[image.sha256] = key
            path = _safe_path(root, key)
            if path.exists():
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_name(path.name + ".partial")
            partial.write_bytes(image.content)
            partials.append(partial)
            partial.replace(path)
            partials.remove(partial)
    return keys


def _workbook_partial(root: Path, job_id: int, source_code: str, content: bytes) -> Path:
    final = _safe_path(root, f"imports/{job_id}/{source_code}.xlsx")
    final.parent.mkdir(parents=True, exist_ok=True)
    partial = final.with_name(final.name + ".partial")
    partial.write_bytes(content)
    return partial


def _source_summary(
    item: dict[str, Any],
    parsed: ParsedWorkbook,
    rows: list[ParsedRow],
    absent: list[int],
) -> dict[str, Any]:
    counts: dict[str, int] = {
        "product": 0,
        "service": 0,
        "heading": 0,
        "blank": 0,
        "stray": 0,
        "invalid": 0,
        "insert": 0,
        "update": 0,
        "unchanged": 0,
        "possible_match": 0,
        "conflict": 0,
        "exclude": 0,
        "skip": 0,
        "numeric_prices": 0,
        "explicit_on_request": 0,
        "blank_prices": 0,
        "brand_unverified": 0,
        "duplicate_model": 0,
        "internal_discount_note": 0,
        "images_extracted": 0,
        "images_rejected": 0,
        "linked_high": 0,
        "linked_review": 0,
        "unassigned": 0,
        "shared_candidate": 0,
        "absent_products": len(absent),
        "trailing_empty_rows": sum(sheet.trailing_empty_rows for sheet in parsed.sheets),
    }
    for row in rows:
        counts[row.classification] = counts.get(row.classification, 0) + 1
        counts[row.action] = counts.get(row.action, 0) + 1
        codes = {str(message.get("code")) for message in row.messages}
        for code in ("brand_unverified", "duplicate_model", "internal_discount_note"):
            if code in codes:
                counts[code] += 1
        if row.classification in {"product", "service"}:
            kind = str(row.proposal["price"]["kind"])
            if kind == "numeric":
                counts["numeric_prices"] += 1
            elif kind == "explicit_on_request":
                counts["explicit_on_request"] += 1
            elif kind == "blank":
                counts["blank_prices"] += 1
    digests: set[str] = set()
    for sheet in parsed.sheets:
        for image in sheet.images:
            if image.rejected:
                counts["images_rejected"] += 1
                continue
            if image.link_status == "shared_candidate":
                counts["shared_candidate"] += 1
                continue
            if image.sha256:
                digests.add(image.sha256)
            if image.link_status in {"linked_high", "linked_review", "unassigned"}:
                counts[image.link_status] += 1
    counts["images_extracted"] = len(digests)
    return {
        "source_code": item["source_code"],
        "original_filename": item["filename"],
        "sha256": item["sha256"],
        "validation_status": "valid",
        "counts": counts,
        "absent_product_ids": absent,
        "sheets": [
            {
                "worksheet": sheet.name,
                "header_row": sheet.header_row,
                "errors": sheet.errors,
                "trailing_empty_rows": sheet.trailing_empty_rows,
            }
            for sheet in parsed.sheets
        ],
    }


def _combine(sources: list[dict[str, Any]]) -> dict[str, int]:
    combined: dict[str, int] = {}
    for source in sources:
        for key, value in source["counts"].items():
            combined[key] = combined.get(key, 0) + int(value)
    return dict(sorted(combined.items()))


def _matched_product(rows: list[ParsedRow], worksheet: str, anchor_row: int | None) -> int | None:
    if anchor_row is None:
        return None
    for row in rows:
        if row.worksheet_name == worksheet and row.source_row == anchor_row:
            if row.action in {"update", "unchanged", "possible_match"}:
                return row.matched_product_id
            return None
    return None


def _ru_name(translations: list[Any]) -> str | None:
    for translation in translations:
        if translation.locale == "ru":
            return translation.name
    return None


def _ru_description(product: Product) -> str | None:
    for translation in product.translations:
        if translation.locale == "ru":
            return translation.description
    return None


def _description_locked(product: Product) -> bool:
    for translation in product.translations:
        if translation.locale == "ru":
            return translation.description_locked
    return False


def _assert_media_root(media_root: Path) -> Path:
    root = media_root.resolve()
    for parent in (root, *root.parents):
        if parent.name.casefold() == "source" and parent.parent.name.casefold() == "data":
            raise StagingError("Refusing to write staged files into data/source.")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_path(root: Path, key: str) -> Path:
    if not key or ".." in key.split("/") or key.startswith(("/", "\\")):
        raise StagingError("Unsafe stored object key.")
    path = (root / key).resolve()
    if path != root and root not in path.parents:
        raise StagingError("Unsafe stored object key.")
    return path


def _basename(filename: str) -> str:
    name = filename.replace("\\", "/").split("/")[-1].strip()
    return (name or "workbook.xlsx")[:255]


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
