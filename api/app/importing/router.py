"""Authenticated import workflow. Reads use require_admin. Writes use require_admin_write."""

from __future__ import annotations

import secrets
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.auth.dependencies import get_db, get_settings_from_request, require_admin, require_admin_write
from app.config import Settings
from app.importing.apply import ApplyError, apply_job, mark_job_failed
from app.importing.stage import SourceInput, StagingError, stage_import
from app.models import AdminUser, ImportAsset, ImportFile, ImportJob, ImportRow

router = APIRouter(prefix="/api/admin/imports", tags=["imports"])
_MAX_FILES = 2
_MAX_PAGE_SIZE = 100
_READ_CHUNK = 1024 * 1024


class RowResolutionBody(BaseModel):
    resolution: str = Field(pattern="^(keep_current|accept_excel|accept_new|exclude)$")


class AssetExclusionBody(BaseModel):
    excluded: bool


class ApplyBody(BaseModel):
    confirm: bool


def _job_or_404(db: Session, job_id: int) -> ImportJob:
    job = db.get(ImportJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Import job not found.")
    return job


def _public_summary(job: ImportJob, files: list[ImportFile]) -> dict[str, object]:
    summary = job.summary or {}
    return {
        "id": job.id,
        "status": job.status,
        "replace_prices": job.replace_prices,
        "publish_new_products": job.publish_new_products,
        "approved_by": job.approved_by,
        "applied_at": job.applied_at.isoformat() if job.applied_at else None,
        "error_message": job.error_message,
        "summary": summary,
        "files": [
            {
                "id": file.id,
                "source_code": file.source_code,
                "original_filename": file.original_filename,
                "sha256": file.sha256.strip(),
                "identification": file.identification,
                "validation_status": file.validation_status,
                "validation_errors": file.validation_errors,
                "included_in_apply": file.included_in_apply,
            }
            for file in files
        ],
        "rejected_files": summary.get("rejected_files") or [],
    }


@router.post("")
def create_import(
    files: list[UploadFile] = File(),
    source_overrides: list[str] | None = Form(default=None),
    replace_prices: bool = Form(default=False),
    publish_new_products: bool = Form(default=True),
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    if not files or len(files) > _MAX_FILES:
        raise HTTPException(status_code=422, detail="Upload one or both source workbooks.")
    root = Path(settings.media_root)
    temp_dir = root / "private-uploads" / secrets.token_hex(16)
    temp_dir.mkdir(parents=True, exist_ok=True)
    sources: list[SourceInput] = []
    try:
        overrides = source_overrides or []
        for index, upload in enumerate(files):
            original_name, stored = _store_upload(upload, temp_dir, settings.import_max_bytes)
            override = overrides[index].strip().casefold() if index < len(overrides) else ""
            if override in {"hikvision", "ezviz"}:
                sources.append(
                    SourceInput(
                        stored,
                        original_name,
                        identification="admin_confirmed",
                        declared_source=override,
                    )
                )
            else:
                sources.append(SourceInput(stored, original_name))
        job = ImportJob(
            created_by=admin.id,
            status="preview",
            replace_prices=replace_prices,
            publish_new_products=publish_new_products,
        )
        db.add(job)
        db.flush()
        try:
            summary = stage_import(db, job, sources, root)
        except StagingError as exc:
            raise HTTPException(status_code=422, detail=exc.args[0]) from exc
        if not summary.get("sources"):
            rejected = summary.get("rejected_files") or []
            job_directory = root / "imports" / str(job.id)
            db.rollback()
            shutil.rmtree(job_directory, ignore_errors=True)
            raise HTTPException(
                status_code=422,
                detail={"message": "The workbook could not be staged.", "rejected_files": rejected},
            )
        db.commit()
        db.refresh(job)
        stored_files = list(db.scalars(select(ImportFile).where(ImportFile.job_id == job.id)).all())
        return _public_summary(job, stored_files)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.get("/{job_id}")
def read_import(
    job_id: int,
    _: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    job = _job_or_404(db, job_id)
    files = list(db.scalars(select(ImportFile).where(ImportFile.job_id == job.id)).all())
    return _public_summary(job, files)


@router.get("/{job_id}/rows")
def read_rows(
    job_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=_MAX_PAGE_SIZE),
    source_code: str | None = Query(default=None),
    action: str | None = Query(default=None),
    _: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    job = _job_or_404(db, job_id)
    file_ids = list(db.scalars(select(ImportFile.id).where(ImportFile.job_id == job.id)).all())
    if source_code is not None:
        file_ids = list(
            db.scalars(
                select(ImportFile.id).where(
                    ImportFile.job_id == job.id,
                    ImportFile.source_code == source_code,
                )
            ).all()
        )
    filters = [ImportRow.import_file_id.in_(file_ids or [-1])]
    if action is not None:
        filters.append(ImportRow.action == action)
    total = db.scalar(select(func.count()).select_from(ImportRow).where(*filters)) or 0
    rows = db.scalars(
        select(ImportRow)
        .where(*filters)
        .order_by(ImportRow.worksheet_name, ImportRow.source_row, ImportRow.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "rows": [_public_row(row) for row in rows],
    }


@router.get("/{job_id}/assets")
def read_assets(
    job_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=_MAX_PAGE_SIZE),
    _: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    job = _job_or_404(db, job_id)
    file_ids = list(db.scalars(select(ImportFile.id).where(ImportFile.job_id == job.id)).all())
    filters = [ImportAsset.import_file_id.in_(file_ids or [-1])]
    total = db.scalar(select(func.count()).select_from(ImportAsset).where(*filters)) or 0
    assets = db.scalars(
        select(ImportAsset)
        .where(*filters)
        .order_by(ImportAsset.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    excluded = set((job.summary or {}).get("excluded_asset_ids") or [])
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "assets": [
            {
                "id": asset.id,
                "sha256": asset.sha256.strip(),
                "mime_type": asset.mime_type,
                "worksheet": asset.worksheet,
                "anchor_row": asset.anchor_row,
                "anchor_col": asset.anchor_col,
                "link_status": asset.link_status,
                "excluded": asset.id in excluded,
            }
            for asset in assets
        ],
    }


@router.patch("/{job_id}/rows/{row_id}")
def resolve_row(
    job_id: int,
    row_id: int,
    body: RowResolutionBody,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    del admin
    job = _job_or_404(db, job_id)
    if job.status != "preview":
        raise HTTPException(status_code=409, detail="Only a preview job can be changed.")
    row = _row_in_job(db, job_id, row_id)
    if row.classification in {"blank", "heading", "stray"} and body.resolution != "exclude":
        raise HTTPException(status_code=409, detail="This row cannot be resolved.")
    effective_action = row.action
    if row.action == "exclude" and body.resolution != "exclude":
        effective_action = str((row.proposal or {}).get("action_before_exclude") or row.action)
    if effective_action == "conflict" and body.resolution in {"accept_excel", "accept_new"}:
        raise HTTPException(status_code=409, detail="A conflicting row cannot choose one Excel value.")
    proposal = dict(row.proposal or {})
    if body.resolution == "exclude":
        proposal.setdefault("action_before_exclude", row.action)
        row.action = "exclude"
        row.resolution = "keep_current"
    else:
        if row.action == "exclude":
            row.action = str(proposal.get("action_before_exclude") or "update")
        row.resolution = body.resolution
        resolutions = dict(proposal.get("field_resolutions") or {})
        if body.resolution == "accept_excel":
            for key, value in list(resolutions.items()):
                if value == "keep_current":
                    resolutions[key] = "accept_excel"
        proposal["field_resolutions"] = resolutions
    row.proposal = proposal
    flag_modified(row, "proposal")
    db.commit()
    return _public_row(row)


@router.post("/{job_id}/assets/{asset_id}/exclusion")
def exclude_asset(
    job_id: int,
    asset_id: int,
    body: AssetExclusionBody,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    del admin
    job = _job_or_404(db, job_id)
    if job.status != "preview":
        raise HTTPException(status_code=409, detail="Only a preview job can be changed.")
    asset = _asset_in_job(db, job_id, asset_id)
    summary = dict(job.summary or {})
    excluded = {int(item) for item in summary.get("excluded_asset_ids") or []}
    if body.excluded:
        excluded.add(asset.id)
    else:
        excluded.discard(asset.id)
    summary["excluded_asset_ids"] = sorted(excluded)
    job.summary = summary
    flag_modified(job, "summary")
    db.commit()
    return {"id": asset.id, "excluded": asset.id in excluded}


@router.post("/{job_id}/apply")
def apply_import(
    job_id: int,
    body: ApplyBody,
    request: Request,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_from_request),
) -> dict[str, object]:
    if not body.confirm:
        raise HTTPException(status_code=422, detail="Confirm the import before applying it.")
    try:
        result = apply_job(
            db,
            job_id,
            admin.id,
            Path(settings.media_root),
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
        return result
    except ApplyError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        db.rollback()
        mark_job_failed(db, job_id)
        db.commit()
        raise HTTPException(status_code=409, detail="The import could not be applied.") from exc


@router.post("/{job_id}/reject")
def reject_import(
    job_id: int,
    admin: AdminUser = Depends(require_admin_write),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    del admin
    job = _job_or_404(db, job_id)
    if job.status != "preview":
        raise HTTPException(status_code=409, detail="Only a preview job can be rejected.")
    job.status = "rejected"
    db.commit()
    return {"id": job.id, "status": job.status}


def _row_in_job(db: Session, job_id: int, row_id: int) -> ImportRow:
    row = db.scalar(
        select(ImportRow)
        .join(ImportFile, ImportRow.import_file_id == ImportFile.id)
        .where(ImportRow.id == row_id, ImportFile.job_id == job_id)
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Import row not found.")
    return row


def _asset_in_job(db: Session, job_id: int, asset_id: int) -> ImportAsset:
    asset = db.scalar(
        select(ImportAsset)
        .join(ImportFile, ImportAsset.import_file_id == ImportFile.id)
        .where(ImportAsset.id == asset_id, ImportFile.job_id == job_id)
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Import asset not found.")
    return asset


def _public_row(row: ImportRow) -> dict[str, object]:
    return {
        "id": row.id,
        "worksheet_name": row.worksheet_name,
        "source_row": row.source_row,
        "classification": row.classification,
        "action": row.action,
        "resolution": row.resolution,
        "matched_product_id": row.matched_product_id,
        "messages": row.messages,
        "proposal": row.proposal,
        "applied": row.applied,
    }


def _store_upload(upload: UploadFile, directory: Path, limit: int) -> tuple[str, Path]:
    filename = (upload.filename or "workbook.xlsx").replace("\\", "/").split("/")[-1][:255]
    target = directory / f"{secrets.token_hex(16)}.xlsx"
    size = 0
    try:
        with target.open("wb") as handle:
            while True:
                chunk = upload.file.read(_READ_CHUNK)
                if not chunk:
                    break
                size += len(chunk)
                if size > limit:
                    raise HTTPException(status_code=413, detail="The workbook is larger than the configured limit.")
                handle.write(chunk)
    except HTTPException:
        target.unlink(missing_ok=True)
        raise
    return filename or "workbook.xlsx", target
