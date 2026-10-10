"""Extract embedded workbook images and classify anchors. Bytes are never written back."""

from __future__ import annotations

import hashlib
import posixpath
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

_PNG = b"\x89PNG\r\n\x1a\n"
_JPEG = b"\xff\xd8\xff"
_EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}


@dataclass(frozen=True)
class ImageAnchor:
    worksheet: str
    index: int
    row: int | None
    col: int | None
    to_row: int | None
    content: bytes


@dataclass(frozen=True)
class AssociatedImage:
    worksheet: str
    index: int
    row: int | None
    col: int | None
    to_row: int | None
    content: bytes
    sha256: str
    mime_type: str | None
    extension: str | None
    link_status: str | None
    rejected: bool
    shared_from_row: int | None = None


def sniff_image(content: bytes) -> str | None:
    """Accept PNG, JPEG, and WebP only after checking the container bytes."""

    if content.startswith(_PNG) and b"IHDR" in content[:24] and content.endswith(b"IEND\xaeB`\x82"):
        return "image/png"
    if content.startswith(_JPEG) and content.endswith(b"\xff\xd9") and len(content) > 4:
        return "image/jpeg"
    if len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        declared = int.from_bytes(content[4:8], "little")
        if declared + 8 == len(content):
            return "image/webp"
    return None


def object_key(digest: str, extension: str) -> str:
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("Image object keys are content hashes")
    if extension not in {"png", "jpg", "webp"}:
        raise ValueError("Unsupported image extension")
    return f"objects/{digest[:2]}/{digest}.{extension}"


_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_OFFICE = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_XDR = "{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}"
_DRAWING_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing"


def read_all_anchors(path: Path) -> tuple[dict[str, list[ImageAnchor]], list[dict[str, str]]]:
    """Read original image bytes from the package. Pillow is not used, so bytes stay unchanged."""

    warnings: list[dict[str, str]] = []
    grouped: dict[str, list[ImageAnchor]] = {}
    try:
        with ZipFile(path) as package:
            names = set(package.namelist())
            sheets = _sheet_paths(package, names)
            for worksheet_name, sheet_path in sheets:
                for anchor in _sheet_anchors(package, names, worksheet_name, sheet_path, warnings):
                    grouped.setdefault(worksheet_name, []).append(anchor)
    except ET.ParseError:
        warnings.append(
            {
                "level": "warning",
                "code": "image_anchors_unreadable",
                "message": "Image anchors could not be read. No image was assigned.",
            }
        )
    return grouped, warnings


def _sheet_paths(package: ZipFile, names: set[str]) -> list[tuple[str, str]]:
    if "xl/workbook.xml" not in names or "xl/_rels/workbook.xml.rels" not in names:
        return []
    workbook = ET.fromstring(package.read("xl/workbook.xml"))
    relationships = _relationship_targets(package.read("xl/_rels/workbook.xml.rels"))
    sheets: list[tuple[str, str]] = []
    for sheet in workbook.findall(f"{_MAIN}sheets/{_MAIN}sheet"):
        name = sheet.attrib.get("name")
        relation = sheet.attrib.get(f"{_OFFICE}id")
        target = relationships.get(relation or "")
        if not name or not target:
            continue
        sheets.append((name, _join("xl/workbook.xml", target)))
    return sheets


def _sheet_anchors(
    package: ZipFile,
    names: set[str],
    worksheet_name: str,
    sheet_path: str,
    warnings: list[dict[str, str]],
) -> list[ImageAnchor]:
    rels_path = _rels_path(sheet_path)
    if rels_path not in names:
        return []
    relationships = _relationship_targets(package.read(rels_path), type_filter=_DRAWING_REL)
    anchors: list[ImageAnchor] = []
    for drawing_target in relationships.values():
        drawing_path = _join(sheet_path, drawing_target)
        if drawing_path not in names:
            warnings.append(
                {
                    "level": "warning",
                    "code": "image_anchors_unreadable",
                    "worksheet": worksheet_name,
                    "message": "A drawing part is missing. Its images were not assigned.",
                }
            )
            continue
        drawing_rels = _rels_path(drawing_path)
        media = _relationship_targets(package.read(drawing_rels)) if drawing_rels in names else {}
        try:
            root = ET.fromstring(package.read(drawing_path))
        except ET.ParseError:
            warnings.append(
                {
                    "level": "warning",
                    "code": "image_anchors_unreadable",
                    "worksheet": worksheet_name,
                    "message": "A drawing part could not be read. Its images were not assigned.",
                }
            )
            continue
        for element in root:
            if not element.tag.endswith("Anchor"):
                continue
            row, column, to_row = _marker(element)
            for picture in element.iter(f"{_XDR}pic"):
                embed = _embed(picture)
                if embed is None:
                    warnings.append(
                        {
                            "level": "warning",
                            "code": "external_image_ignored",
                            "worksheet": worksheet_name,
                            "message": "An image is linked outside the workbook and was not imported.",
                        }
                    )
                    continue
                target = media.get(embed)
                if target is None:
                    continue
                media_path = _join(drawing_path, target)
                if media_path not in names:
                    continue
                anchors.append(
                    ImageAnchor(
                        worksheet=worksheet_name,
                        index=len(anchors),
                        row=row,
                        col=column,
                        to_row=to_row,
                        content=package.read(media_path),
                    )
                )
    return anchors


def associate_images(
    anchors: list[ImageAnchor],
    *,
    model_rows: set[int],
    photo_column: int | None,
    photo_merges: list[tuple[int, int, int, int]],
) -> list[AssociatedImage]:
    """Apply the anchor rules. A tall image does not belong to the next row."""

    associated: list[AssociatedImage] = []
    for anchor in anchors:
        mime = sniff_image(anchor.content)
        if mime is None:
            associated.append(_associated(anchor, mime=None, status=None, rejected=True))
            continue
        if anchor.row is None or anchor.row not in model_rows:
            status = "unassigned"
        elif photo_column is not None and anchor.col == photo_column:
            status = "linked_high"
        else:
            status = "linked_review"
        associated.append(_associated(anchor, mime=mime, status=status, rejected=False))

    shared: list[AssociatedImage] = []
    for min_row, min_col, max_row, max_col in photo_merges:
        if photo_column is None or not (min_col <= photo_column <= max_col):
            continue
        covered = [row for row in range(min_row, max_row + 1) if row in model_rows]
        if len(covered) < 2:
            continue
        donors = [
            image
            for image in associated
            if image.link_status == "linked_high"
            and image.row in covered
            and image.col == photo_column
        ]
        owner_rows = {image.row for image in donors}
        for row in covered:
            if row in owner_rows:
                continue
            for donor in donors:
                shared.append(
                    AssociatedImage(
                        worksheet=donor.worksheet,
                        index=donor.index,
                        row=row,
                        col=photo_column,
                        to_row=max_row,
                        content=donor.content,
                        sha256=donor.sha256,
                        mime_type=donor.mime_type,
                        extension=donor.extension,
                        link_status="shared_candidate",
                        rejected=False,
                        shared_from_row=donor.row,
                    )
                )
    return associated + shared


def _associated(
    anchor: ImageAnchor,
    *,
    mime: str | None,
    status: str | None,
    rejected: bool,
) -> AssociatedImage:
    digest = hashlib.sha256(anchor.content).hexdigest() if not rejected else ""
    return AssociatedImage(
        worksheet=anchor.worksheet,
        index=anchor.index,
        row=anchor.row,
        col=anchor.col,
        to_row=anchor.to_row,
        content=anchor.content,
        sha256=digest,
        mime_type=mime,
        extension=_EXTENSIONS.get(mime or ""),
        link_status=status,
        rejected=rejected,
    )


def _relationship_targets(payload: bytes, type_filter: str | None = None) -> dict[str, str]:
    root = ET.fromstring(payload)
    found: dict[str, str] = {}
    for child in root:
        if type_filter is not None and child.attrib.get("Type") != type_filter:
            continue
        relation_id = child.attrib.get("Id")
        target = child.attrib.get("Target")
        if relation_id and target:
            found[relation_id] = target
    return found


def _rels_path(part: str) -> str:
    directory, name = posixpath.split(part)
    return posixpath.join(directory, "_rels", f"{name}.rels")


def _join(base: str, target: str) -> str:
    target = target.replace("\\", "/")
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(base), target))


def _marker(anchor: ET.Element) -> tuple[int | None, int | None, int | None]:
    origin = anchor.find(f"{_XDR}from")
    if origin is None:
        return None, None, None
    row = _child_int(origin, "row")
    column = _child_int(origin, "col")
    target = anchor.find(f"{_XDR}to")
    to_row = _child_int(target, "row") if target is not None else None
    if row is None or column is None:
        return None, None, None
    return row + 1, column + 1, None if to_row is None else to_row + 1


def _child_int(parent: ET.Element, name: str) -> int | None:
    child = parent.find(f"{_XDR}{name}")
    if child is None or child.text is None:
        return None
    try:
        return int(child.text)
    except ValueError:
        return None


def _embed(picture: ET.Element) -> str | None:
    for element in picture.iter(f"{{http://schemas.openxmlformats.org/drawingml/2006/main}}blip"):
        embed = element.attrib.get(f"{_OFFICE}embed")
        if embed:
            return embed
    return None
