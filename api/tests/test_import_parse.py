import hashlib
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

from openpyxl import Workbook

from app.importing.images import ImageAnchor, associate_images, object_key, sniff_image
from app.importing.normalize import classify_price, detect_brands, normalize_model
from app.importing.parse import container_errors, read_workbook
from tests.import_builders import ezviz_workbook, hikvision_workbook, png_bytes

REPO_ROOT = Path(__file__).resolve().parents[2]
HIKVISION_SHA = "8B3CDE12879215CD2E28CCB9ABFACF61F305BA9320B400FF50ACB5403463FCAC"
EZVIZ_SHA = "C4C3D2D4A3A36FB591C58B26FC21274E27E13D2150CEDEEAC0161C4D9566CDA5"


def _by_model(parsed, model: str):
    return [
        row
        for sheet in parsed.sheets
        for row in sheet.rows
        if row.proposal.get("model_raw") == model or row.proposal.get("model_display") == model
    ]


def test_zip_names_with_parent_segments_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.xlsx"
    with ZipFile(path, "w") as package:
        package.writestr("xl/workbook.xml", "<workbook/>")
        package.writestr("xl/../outside.xml", "<outside/>")
    errors = container_errors(path)
    assert errors[0]["code"] == "invalid_zip"


def test_price_rules_keep_blank_request_and_decimal_distinct() -> None:
    blank = classify_price(None, missing_cache=False)
    explicit = classify_price(" По запросу ", missing_cache=False)
    numeric = classify_price(92.5, missing_cache=False)
    tenth = classify_price(0.1, missing_cache=False)
    missing = classify_price(None, missing_cache=True)
    assert blank["kind"] == "blank" and blank["amount"] is None
    assert blank["public_status"] == "on_request"
    assert explicit["kind"] == "explicit_on_request" and explicit["public_amount"] is None
    assert explicit["raw"] == " По запросу "
    assert numeric["amount"] == "92.50" and numeric["currency"] == "USD"
    assert tenth["amount"] == "0.10"
    assert missing["issue"] == "formula_without_cache"
    assert missing["amount"] != "0.00"


def test_brand_detection_uses_text_not_a_short_token_inside_another_word() -> None:
    assert detect_brands("HiLook IPC-1", None) == ["HiLook"]
    assert detect_brands("WD Purple", None) == ["WD"]
    assert detect_brands("FORWARD cam", None) == []
    assert detect_brands("HiLook Hikvision combo", None) == ["HiLook", "Hikvision"]
    assert normalize_model("DS80HKVS\u2010VX1") == "ds80hkvs-vx1"


def test_hikvision_rows_prices_and_headings(tmp_path: Path) -> None:
    path = tmp_path / "Hikvision pr.xlsx"
    hikvision_workbook(path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    parsed = read_workbook(path, "hikvision")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before

    hilook = next(sheet for sheet in parsed.sheets if sheet.name == "Hilook")
    classes = [row.classification for row in hilook.rows]
    assert classes.count("heading") == 2
    assert "blank" in classes
    parent = next(row for row in hilook.rows if row.proposal.get("heading_text") == "Turbo HD камера")
    assert parent.proposal["category_proposal"]["role"] == "parent"
    priced = _by_model(parsed, "HiLook IPC-1")[0]
    assert priced.classification == "product"
    assert priced.proposal["price"]["amount"] == "115.00"
    assert priced.proposal["internal_note"] == "текущая цена со скидкой 60$"
    assert {"code": "internal_discount_note"} in priced.messages
    assert priced.proposal["brand"] == "HiLook"
    assert priced.proposal["section_label"] == "ColorVu"
    assert priced.proposal["parent_section_label"] == "Turbo HD камера"
    assert priced.proposal["initial_stock_status"] == "in_stock"
    assert len(priced.proposal["images"]) == 2
    assert priced.proposal["images"][0]["proposed_primary"] is True
    assert priced.proposal["images"][0]["link_status"] == "linked_high"

    blank_price = _by_model(parsed, "plain cam")[0]
    assert blank_price.proposal["price"]["kind"] == "blank"
    assert blank_price.proposal["price"]["public_amount"] is None
    assert blank_price.proposal["brand"] is None
    assert {"code": "brand_unverified"} in blank_price.messages

    requested = _by_model(parsed, "DS-1")[0]
    assert requested.proposal["price"]["kind"] == "explicit_on_request"
    assert requested.proposal["price"]["public_status"] == "on_request"

    ambiguous = _by_model(parsed, "HiLook Hikvision combo")[0]
    assert ambiguous.proposal["brand"] is None
    assert {"code": "brand_ambiguous"} in ambiguous.messages

    cameras = next(sheet for sheet in parsed.sheets if sheet.name == "IP камеры")
    assert [row.classification for row in cameras.rows].count("stray") == 1
    bnc = [row for row in cameras.rows if row.proposal.get("model_display") == "BNC"]
    assert len(bnc) == 2
    assert bnc[0].proposal["match_key"] != bnc[1].proposal["match_key"]
    dashed = _by_model(parsed, "DS80HKVS\u2010VX1")[0]
    assert dashed.proposal["model_normalized"] == "ds80hkvs-vx1"
    assert dashed.proposal["model_raw"] == "DS80HKVS\u2010VX1"

    invalid = next(row for row in parsed.sheets if row.name == "PTZ").rows[0]
    assert invalid.classification == "invalid"
    assert invalid.raw_cells["price"]["cached"] is None
    assert "0.00" not in str(invalid.proposal)
    notes = next(sheet for sheet in parsed.sheets if sheet.name == "Notes")
    assert notes.header_row is None
    assert notes.errors[0]["code"] == "missing_required_header"


def test_ezviz_dealer_price_services_and_repeated_models(tmp_path: Path) -> None:
    path = tmp_path / "Ezviz pr.xlsx"
    ezviz_workbook(path)
    parsed = read_workbook(path, "ezviz")
    sheet = parsed.sheets[0]
    assert all(row.classification != "heading" for row in sheet.rows)
    dealer = _by_model(parsed, "CS-DP2C")[0]
    assert dealer.proposal["price"]["header"] == "Цена для дилера"
    assert dealer.proposal["price"]["amount"] == "92.50"
    assert dealer.proposal["brand"] == "EZVIZ"
    assert dealer.proposal["option_label"] == "с солнечной панель"
    assert dealer.proposal["category_name"] == "Ezviz"
    repeated = [row for row in sheet.rows if row.proposal.get("model_display") == "CS-H8C"]
    assert len(repeated) == 2
    assert repeated[0].proposal["match_key"] != repeated[1].proposal["match_key"]
    services = [row for row in sheet.rows if row.classification == "service"]
    assert len(services) == 2
    assert {row.proposal["option_label"] for row in services} == {"Ежемесячно:", "Ежегодно:"}
    shared = next(row for row in services if row.proposal["option_label"] == "Ежегодно:")
    assert shared.proposal["images"][0]["link_status"] == "shared_candidate"
    owner = next(row for row in services if row.proposal["option_label"] == "Ежемесячно:")
    assert owner.proposal["images"][0]["link_status"] == "linked_high"


def test_anchor_rules_do_not_guess_overlap_or_accept_other_formats() -> None:
    png = png_bytes(4)
    tall = ImageAnchor("Sheet", 0, 3, 2, 5, png)
    tall_result = associate_images([tall], model_rows={3, 4}, photo_column=2, photo_merges=[])
    assert [(item.row, item.link_status) for item in tall_result] == [(3, "linked_high")]

    shared = ImageAnchor("Sheet", 0, 3, 2, None, png)
    shared_result = associate_images(
        [shared],
        model_rows={3, 4},
        photo_column=2,
        photo_merges=[(3, 2, 4, 2)],
    )
    assert [(item.row, item.link_status) for item in shared_result] == [
        (3, "linked_high"),
        (4, "shared_candidate"),
    ]
    review = ImageAnchor("Sheet", 1, 3, 4, None, png)
    review_result = associate_images([review], model_rows={3}, photo_column=2, photo_merges=[])
    assert review_result[0].link_status == "linked_review"
    rejected = associate_images(
        [ImageAnchor("Sheet", 2, 3, 2, None, b"GIF89a" + b"\x00" * 12)],
        model_rows={3},
        photo_column=2,
        photo_merges=[],
    )
    assert rejected[0].rejected is True
    assert sniff_image(png) == "image/png"
    digest = shared_result[0].sha256
    assert object_key(digest, "png") == f"objects/{digest[:2]}/{digest}.png"


def test_unexpected_header_and_formula_file_are_explicit(tmp_path: Path) -> None:
    path = tmp_path / "broken.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Custom"
    sheet.append(["Название", "Стоимость"])
    sheet.append(["камера", 10])
    workbook.save(path)
    workbook.close()
    parsed = read_workbook(path, "hikvision")
    assert parsed.has_required_sheet is False
    assert parsed.errors[0]["code"] == "missing_required_header"


def test_real_workbooks_stay_byte_for_byte_unchanged() -> None:
    hikvision = REPO_ROOT / "data" / "source" / "Hikvision pr.xlsx"
    ezviz = REPO_ROOT / "data" / "source" / "Ezviz pr.xlsx"
    if not hikvision.is_file() or not ezviz.is_file():
        return
    before = {
        hikvision: hashlib.sha256(hikvision.read_bytes()).hexdigest(),
        ezviz: hashlib.sha256(ezviz.read_bytes()).hexdigest(),
    }
    assert before[hikvision] == HIKVISION_SHA.casefold()
    assert before[ezviz] == EZVIZ_SHA.casefold()
    hikvision_parsed = read_workbook(hikvision, "hikvision")
    ezviz_parsed = read_workbook(ezviz, "ezviz")
    assert hashlib.sha256(hikvision.read_bytes()).hexdigest() == before[hikvision]
    assert hashlib.sha256(ezviz.read_bytes()).hexdigest() == before[ezviz]
    rows = [row for parsed in (hikvision_parsed, ezviz_parsed) for sheet in parsed.sheets for row in sheet.rows]
    assert sum(row.classification in {"product", "service"} for row in rows) == 639
    assert sum(row.classification == "heading" for row in rows) == 28
    assert sum(row.classification == "stray" for row in rows) == 3
    assert sum(row.classification == "service" for row in rows) == 4
    prices = [
        row.proposal["price"]["kind"]
        for row in rows
        if row.classification in {"product", "service"}
    ]
    assert prices.count("numeric") == 587
    assert prices.count("explicit_on_request") == 42
    assert prices.count("blank") == 10
    images = [image for parsed in (hikvision_parsed, ezviz_parsed) for sheet in parsed.sheets for image in sheet.images if not image.rejected and image.link_status != "shared_candidate"]
    assert len(images) == 762
