# Unresolved draft products

Read-only inspection of `data/source/Hikvision pr.xlsx` and `data/source/Ezviz pr.xlsx` on 17 October 2026. The workbooks were opened and not saved. Excel row numbers below are the worksheet row numbers, not the value in column A and not the database id.

None of these model strings occur in `Ezviz pr.xlsx`. Every located row is in `Hikvision pr.xlsx`. Column C is the model, column D is the description, and column E is the price. Images are drawings anchored on column B, not cell values.

Products 13–17 and 528 were published on 17 October with the approved descriptions. Products 268, 494, and 533 were published earlier the same day. No drafts remain.

## Source locations

| Product | Sheet | Row | Model cell | Description cell | Price cell |
| --- | --- | --- | --- | --- | --- |
| 13 Seagate 500GB | HDD | 12 | `C12` `Seagate  500GB` | empty | `E12` 18 |
| 14 Seagate 1TB | HDD | 13 | `C13` `Seagate  1TB` | empty | `E13` 56 |
| 15 Seagate 2TB | HDD | 14 | `C14` `Seagate  2TB` | empty | `E14` 75 |
| 16 Seagate 4TB | HDD | 15 | `C15` `Seagate  4TB` | empty | `E15` 135 |
| 17 Seagate 6TB | HDD | 16 | `C16` `Seagate  6TB` | empty | `E16` 200 |
| 268 `DS-2SE4C425MWG-E 14` | PTZ | 9 | `C9` `DS-2SE4C425MWG-E  14` | `D9`, quoted below | `E9` 360 |
| 494 `GDR-126035B` | другие устройства | 41 | `C41` `GDR-126035B` | `D41` `Network Communication Cabinet GDR-126035BM  19  12U  600x350x635mm.` | `E41` 90 |
| 528 `гибкий переход` | другие устройства | 75 | `C75` `гибкий переход` | `D75` `гибкий переход` | `E75` 1.5 |
| 533 `2V 15A` | другие устройства | 80 | `C80` `2V 15A` | `D80` `Блок питания, рабочее напряжение: 110V/220V± 15%, выходное напряжение: 12V, выходной ток: 15A` | `E80` 5 |

Neighboring HDD rows do contain manufacturer-style part numbers, including `WD30PURX-78` and `DS-20HKVS-VXI`. The five Seagate rows do not. Their descriptions are empty.

## Images

The five Seagate drawings, HDD rows 12–16, are byte-identical: 72,297 bytes, SHA-256 `5c230e2a0fd834e9fac25dc6c9ac367f226bb227a4c471cbc89fa2b9b7e16757`. The workbook does not establish a distinct photo or a Seagate part number for any capacity. In the catalog, only product 14 is associated with that image.

PTZ row 8, published product 267 `DS-2SE4C415MWG-E 14FO`, has a drawing of 11,882 bytes, SHA-256 `ea282f0f026124046738ce22663dbad0bbae2e0d77b88bbf0bea2825dd959217`. PTZ row 9, product 268, repeats that same drawing. A second drawing spans rows 4–9 (5,572 bytes, SHA-256 `26b0863c531aedee749a3f058772e0cb2433e51b41e50e4a653e92c5addef9d1`) and is not the associated product image. The shared file must stay, because product 267 uses it.

`GDR-126035B` has no drawing that starts and ends on row 41. Several cabinet drawings start at row 36, 37, or 39 and merely pass across row 41. Product 494 has no product image.

`гибкий переход` has a drawing that starts and ends on row 75: 1,753 bytes, SHA-256 `8b7cb283a96e19ed345a83dba277fbf89d2c02c44c22bf5d74697998708f6dd8`. That is the image stored for product 528. A second drawing spans rows 73–75 and belongs to the connector group above it.

`2V 15A` has no drawing of its own. One drawing spans rows 77–82, SHA-256 `d35a89f56380a253ed1280c52c83e4bdd1615ed193b52a1a294d1d35e3d90dd5`.

## Conflicts that block publication

**268.** `D9` begins `TandemVu 4+4MP 25x` and later says `с 15-кратным оптическим зумом и 16-кратным цифровым зумом`. The published text keeps that 15× optical and 16× digital sentence and does not repeat the 25× title. The drawing anchored on row 9 is byte-identical to row 8, so the existing image is the source image.

**494.** The model cell ends in `B`. The description names `GDR-126035BM`. The sheet does not say glass, metal, or any other door type. Sibling rows `GDR-66035B` and `GDR-96035B` use `B` in both the model and the description, and they include `19` before the U size. `GDR-186035B` uses `B` and omits `19`. The `19` is the rack notation used by those siblings, not a documented door difference. Product 494 stays in the published cabinet category `kommunikatsionnye-shkafy`. The published description uses `GDR-126035B` and does not name a door type. No spanning cabinet drawing was attached.

**533.** The model cell says `2V 15A`. The description says output voltage 12V and output current 15A. The rows around it are `12V 5A`, `12V 10A`, `12V 20A`, and `12V 30A`. The model text and the output voltage disagree. The approved catalog model is `12V 15A`; the workbook cell was not edited. No neighboring power-supply drawing was attached.

**13–17.** Capacity and a USD amount are present. An exact Seagate model and a distinct image are not.

## `гибкий переход`

Product 528 is in category 38, slug `drugie-ustroystva`, whose source worksheet and heading are `другие устройства`. It is the category's only product. The category and the product are now published. The public price remains 1.50 USD, the dedicated row-75 image remains, and the brand is still empty. The approved descriptions replaced the name-only text in Russian, Uzbek, and English. No model, brand, or technical specification was invented.

## Decisions

| ID | Status | Confirmed | Missing or conflicting | Decision needed | Manufacturer documentation |
| --- | --- | --- | --- | --- | --- |
| 13 | published | HDD row 12, Seagate, category HDD, $18, no image | No part number | Resolved with the approved capacity description. No image was added | No |
| 14 | published | HDD row 13, $56, the shared Seagate drawing | No part number | Resolved. The existing row image was kept | No |
| 15 | published | HDD row 14, $75, no image | No part number | Resolved with the approved description. No image was added | No |
| 16 | published | HDD row 15, $135, no image | No part number | Resolved with the approved description. No image was added | No |
| 17 | published | HDD row 16, $200, no image | No part number | Resolved with the approved description. No image was added | No |
| 268 | published | PTZ row 9, Hikvision, $360. The row-9 drawing is the stored image | The source title said 25×; the published text keeps the explicit 15× optical and 16× digital sentence | Resolved by the approved text. No separate photo exists in the workbook | Not needed for the approved text |
| 494 | published | другие устройства row 41, cabinet category, $90, model `GDR-126035B` | No door type and no drawing anchored on row 41 | Resolved. Published without an image or a door-type claim | Not needed |
| 528 | published | другие устройства row 75, category 38, $1.50, dedicated image | No brand or part number | Resolved with the approved description. Category 38 is published | No |
| 533 | published as `12V 15A` | другие устройства row 80, power-supply category, $5 | The workbook model cell still says `2V 15A`; the approved catalog model is `12V 15A` | Resolved. Published without a neighboring power-supply image | Not needed |

## Test records removed

Products 1 (`TEST-DO-NOT-SELL-001`, archived) and 2 (`ddmlwefwe`, draft) were deleted through `POST /api/admin/products/{id}/delete` after the model string was checked. They had no images and no source records. Audit rows 9, 10, and 13 remain, with new `product_deleted` rows 1619 and 1620. Immediately after that deletion the catalog had 630 published products and 9 drafts. The later approved publications left 639 published products and no drafts.
