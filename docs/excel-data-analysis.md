# Excel data analysis

Read-only inspection of the two workbooks in `data/source/`. The files were not modified.

The repository does not contain `reports/workbook-analysis/` or `scripts/analyze_workbooks.py`. The figures below were calculated with openpyxl from cached cell values and drawing anchors. They replace the preliminary totals named in the task brief. Those preliminary totals are reconciled at the end of this document.

No formula cells were found. The `Фото` column has no cell values on any sheet. Photographs are drawing objects anchored to cells.

## Corpus

| File | Size | Worksheets |
| --- | --- | --- |
| `Ezviz pr.xlsx` | 4.7 MB | 1 |
| `Hikvision pr.xlsx` | 18.3 MB | 11 |

Twelve worksheets. Embedded images: **762**. Decoded image bytes are about 34 MB. Formats are PNG, JPEG, and WebP only.

A **model row** is a non-header row whose model cell is non-empty. There are **639** model rows. That is the candidate product population. It is not yet an approved published count: service rows and possible duplicates stay in the population as separate records, and the administrator approves the import.

## Worksheets

| Workbook | Worksheet | Sheet size | Header row | Model rows | Numeric prices | `По запросу` | Blank price | No description | Section labels | Stray rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EZVIZ | Ezviz | 582 × 48 | 2 | 84 | 84 | 0 | 0 | 4 | 0 | 0 |
| Hikvision | Hilook | 137 × 6 | 1 | 106 | 106 | 0 | 0 | 0 | 28 | 0 |
| Hikvision | IP камеры | 119 × 6 | 1 | 116 | 116 | 0 | 0 | 0 | 0 | 2 |
| Hikvision | NVR | 23 × 5 | 1 | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| Hikvision | PTZ | 24 × 5 | 1 | 20 | 16 | 4 | 0 | 0 | 0 | 0 |
| Hikvision | Проектное оборудование | 37 × 6 | 1 | 33 | 2 | 31 | 0 | 0 | 0 | 0 |
| Hikvision | Домофоны | 30 × 6 | 1 | 29 | 29 | 0 | 0 | 0 | 0 | 0 |
| Hikvision | СКУД | 55 × 5 | 1 | 52 | 45 | 7 | 0 | 10 | 0 | 0 |
| Hikvision | Коммутаторы | 32 × 5 | 1 | 26 | 26 | 0 | 0 | 0 | 0 | 0 |
| Hikvision | HDD | 18 × 5 | 1 | 16 | 6 | 0 | 10 | 6 | 0 | 1 |
| Hikvision | Звуковое оборудование | 38 × 7 | 1 | 34 | 34 | 0 | 0 | 0 | 0 | 0 |
| Hikvision | другие устройства | 104 × 6 | 1 | 103 | 103 | 0 | 0 | 0 | 0 | 0 |
| **Total** | | | | **639** | **587** | **42** | **10** | **20** | **28** | **3** |

`587 + 42 + 10 = 639`. Every model row has exactly one of those price states.

Declared dimensions overstate the data:

- EZVIZ uses columns A–F only. Columns G–AV are empty. About 497 rows after the product table are empty. The used range is inflated by formatting or anchors, not by more products.
- Several Hikvision sheets declare a sixth or seventh column that is empty. The exception is Hilook column F, described below.
- Hikvision sheet `Звуковое оборудование` declares 7 columns; values stop at column E.

## Column structures

EZVIZ, header on row 2:

| Column | Header | Filled below the header |
| --- | --- | --- |
| A | № | 81 |
| B | Фото | 0 cell values; images are anchored here and nearby |
| C | Модель | 84 |
| D | Характеристика | 80 |
| E | Доп-опция | 11 |
| F | Цена для дилера | 84, all numeric |

Hikvision product sheets, header on row 1:

| Column | Header | Role |
| --- | --- | --- |
| A | № | Sequence label. Restarts inside Hilook. Not an id |
| B | Фото | Empty cells. Image anchors |
| C | Модель | Product identity text |
| D | Характеристика | Russian prose description |
| E | Цена | Number, blank, or `По запросу` |

Hilook column F has no header (`F1` is empty). The worksheet has no comments. A full-sheet search for `скид` found exactly four cell values, and no comment text:

| Cell | Model cell | Main price (`Цена`) | Column F value |
| --- | --- | --- | --- |
| `F103` | `C103` `DVR-108U-M1 (S)` plus a line break and `AcuSense` | `E103` = 115 | `текущая цена со скидкой 60$` |
| `F106` | `C106` `DVR-208U-M1` | `E106` = 115 | `текущая цена со скидкой 60$` |
| `F107` | `C107` `DVR-216U-M2` | `E107` = 200 | `текущая цена со скидкой 100$` |
| `F115` | `C115` `PTZ-P332ZI-DE3` | `E115` = 200 | `текущая цена со скидкой 100$` |

These are ordinary cell values. The main price is column E. Column F is an internal note. The public price is 115, 115, 200, and 200 USD. The site does not show or apply 60 or 100.

## Price patterns

- Numeric prices are real Excel numbers, not text with separators. Most are integers. **32** are fractional, including EZVIZ `CS-DP2C` at 92.5, four Hilook prices (26.5, 18.5, 6.5, 7.5), one audio price (7.7), and 26 accessory prices on `другие устройства`.
- The only non-numeric price text is ` По запросу ` (leading and trailing space), **42** cells: PTZ 4, project equipment 31, СКУД 7. No other spelling occurs.
- Blank prices: **10**, all on `HDD` (five WD Purple rows and five Hikvision drive rows). Six other HDD rows have numeric prices and no description (five Seagate rows and `DS-10HKVS-VX1 1TB`).
- No zero prices and no negative prices. The smallest amounts are accessory unit prices on `другие устройства` (0.1, 0.14, 0.15, 0.6, 0.75). They are real numbers and must be stored as decimals.
- Project equipment is mostly `По запросу`. Two rows are numeric: `DS-1005KI` at 145 and `DS-1200KI(B)` at 215.
- No price cell contains a currency code or symbol. The only `$` characters are inside the four Hilook notes listed above. The business has since confirmed that every numeric catalog price is USD. That confirmation is a display and storage rule. It is not a currency code found in the price cells, and it is not a conversion.
- Observed numeric ranges: EZVIZ 3–260, Hilook 6.5–260, IP cameras 38–260, NVR 40–600, PTZ 133–700, project equipment 145–215, doorphones 7–240, СКУД 32–2200, switches 12–340, HDD 18–200, audio 7.7–640, other devices 0.1–570.

EZVIZ `Цена для дилера` is present for all 84 model rows and is the confirmed initial public price, displayed in USD.

Public initialization, which does not change the source counts above:

- A numeric cell stays a numeric USD price.
- An explicit `По запросу` cell stays the request-price state.
- A blank price cell is still recorded as blank in provenance, and its public status is initialized to the same request-price state. It is not stored as zero. The 10 blank HDD prices remain blank in the source snapshot.

## Missing values

- Descriptions are missing on 20 model rows: 4 EZVIZ service rows, 10 СКУД rows (turnstiles and related models such as the `DS-K6B411TMX`, `DS-K3B501SX`, `DS-K3B211LX`, `DRT-ES3216`, and `DS-TMG320` lines), and 6 HDD rows.
- Three EZVIZ model rows have an empty `№` cell. The number is not required.
- Empty description or empty price does not remove the row from the candidate set.

## Section headings and stray rows

Hilook has **28** single-cell labels in column A. They are not models. **106** products sit between them. Four labels have no products of their own and act as group titles for the labels that follow: `Turbo HD камера`, `NVR`, `DVR`, and `PTZ`. Examples of labels that do contain products: `ColorVu` (13), `ИК-мини-пуля серии B1` (13), `HiLook Super Eco` (11), `домофоны` (5), `Сетевой коммутаторы` (10).

That parent/child reading is a positional heuristic. The import preview must show it. It must not invent extra products from the labels.

Stray cells, not headings and not products:

- `IP камеры` rows 2 and 13 contain only `1` and `11`.
- `HDD` row 18 contains only `17`.

EZVIZ has no section-label rows.

## Service and variant rows

Four EZVIZ rows, 83–86, have no `CS-` model and no description. They are cloud-history plans:

| Source row | Model | Option | Price |
| --- | --- | --- | --- |
| 83 | 7-дневная видеоистория событий | Ежемесячно: | 3 |
| 84 | 30-дневная видеоистория событий | Ежемесячно: | 5 |
| 85 | 7-дневная видеоистория событий | Ежегодно: | 30 |
| 86 | 30-дневная видеоистория событий | Ежегодно: | 50 |

Cells `A83:A86` and `B83:B86` are merged. The model text is repeated per row, so each row is its own record. The shared photo merge is an image-association warning, not a reason to collapse the rows.

Seven earlier EZVIZ cameras use `Доп-опция` = `с солнечной панель`. That text is a public variant note. The option spelling is preserved.

## Repeated models

After trimming and removing all whitespace, four model strings occur twice. None should be merged.

| Normalized model | Where | How they differ |
| --- | --- | --- |
| `cs-h8c(3mp)` | EZVIZ rows 35 and 38 | Same price (50). Descriptions are close but not the same length (366 vs 371 characters) |
| `7-дневнаявидеоисториясобытий` | EZVIZ rows 83 and 85 | Option and price differ: monthly 3 vs yearly 30 |
| `30-дневнаявидеоисториясобытий` | EZVIZ rows 84 and 86 | Option and price differ: monthly 5 vs yearly 50 |
| `bnc` | `другие устройства` rows 68 and 69 | Same price (0.15). Descriptions differ: a full connector sentence versus `Разъем BNC` |

No cross-sheet model collision appeared under that whitespace-folded comparison. A looser comparison that removes punctuation would create false collisions and must not be used as a merge rule.

Model cells often contain irregular internal spaces (`CS-H6C pro   (1080P)`, `DS-2SE4C415MWG-E           14FO`). Display text collapses whitespace. The raw cell is kept. One HDD model uses a non-ASCII hyphen (`DS80HKVS‐VX1`). The raw character stays in `model_raw`.

## Brands implied by the sheets

The workbook does not have a brand column.

- EZVIZ sheet: models are overwhelmingly `CS-…`. Brand proposal `EZVIZ`.
- Hilook sheet: brand proposal `HiLook`. The sheet also contains NVR, DVR, PTZ, doorphones, and switches under section labels, so the sheet is not one category.
- Other Hikvision sheets: default brand proposal `Hikvision`.
- Exceptions inside those sheets: WD Purple and Seagate on `HDD`; Andel and Cougar locks on `другие устройства`; generic accessories (BNC, HDMI, power supplies, electromagnetic locks) with no manufacturer in the model. These need a brand suggestion plus review, not a silent global brand.

## Embedded images

| Worksheet | Images | Products with an image starting on their row | Products with no image starting on their row | Images on a non-product row | Largest stack starting on one row |
| --- | --- | --- | --- | --- | --- |
| Ezviz | 106 | 78 | 6 | 1 (row 1, column C) | 3 |
| Hilook | 145 | 91 | 15 | 7, including heading rows and anchors past the last product (rows 137–151) | 5 |
| IP камеры | 138 | 116 | 0 | 0 | 5 |
| NVR | 21 | 20 | 0 | 0 | 2 |
| PTZ | 28 | 20 | 0 | 0 | 4 |
| Проектное оборудование | 46 | 33 | 0 | 2 (rows 35–36, below the last model) | 3 |
| Домофоны | 35 | 28 | 1 | 0 | 3 |
| СКУД | 42 | 41 | 11 | 0 | 2 |
| Коммутаторы | 33 | 26 | 0 | 1 (header row) | 3 |
| HDD | 16 | 16 | 0 | 0 | 1 |
| Звуковое оборудование | 35 | 34 | 0 | 0 | 2 |
| другие устройства | 117 | 68 | 35 | 0 | 27 |
| **Total** | **762** | **571** | **68** | **10** | |

HDD is the clean case: 16 products, 16 JPEG anchors, all in column B, each confined to its own row.

The other sheets are not clean:

- Many anchors are taller than one row. A tall photo often overlaps the next product even when that product has its own photo. Overlap is not ownership.
- Merged photo cells group several models under one picture. Examples: EZVIZ `B83:B86` (the four service rows), СКУД merges such as `B31:B33` and `B35:B37`, and several tall merges on `другие устройства` (`B48:B57`, `B76:B83`, `B87:B93`, and others).
- Images also start in columns A, C, D, and, once on PTZ, column H. Column B is the photo column and is the only high-confidence anchor column. Column C/D images may be extra photos or decorative drawings.
- `другие устройства` row 36 starts **27** images, some of whose anchors extend across as many as 12 following product rows. That cluster cannot be auto-assigned by row order.
- Treating every overlapped row as “has an image” would mark only 15 products uncovered and would also attach shared pictures to the wrong models. That interpretation is rejected.
- Treating only the anchor’s starting row as the owner leaves **68** products without a directly started image. Some of those sit inside a merged photo range and should be reported as shared-image candidates, not as confirmed photos and not as deleted products.

Merged-cell samples that matter: EZVIZ `A1:F1` (title band, plus the row 1 image), EZVIZ `A83:A86` and `B83:B86`, Hilook heading merges across `A:E`, СКУД photo merges, `другие устройства` photo merges. EZVIZ also has empty merges `I29:I30` and `J29:J30` with no values. They carry no catalog data.

## What cannot be represented if the model is too strict

The schema in `docs/database-design.md` can hold every observed source fact:

- Repeated models stay on separate product rows.
- Service rows use `product_kind = service` and `option_label`.
- Source kind still distinguishes blank, explicit `По запросу`, and numeric. The public status initialized from a blank cell is the request-price state, with a null amount, while the source row keeps `blank`.
- Fractional prices fit `numeric(12,2)`.
- Missing descriptions stay null.
- Section labels become category proposals plus `section_label` provenance.
- Discount notes fit `internal_note` and are not required to explain the public price.
- Multiple images, missing images, and ambiguous anchors fit image rows and import-asset statuses.
- Raw model whitespace and the original description are retained beside normalized fields.

No source column requires a second public price, a stock quantity, or a tax amount. None of those concepts appear in the files.

## Reconciliation with the preliminary analyzer totals

| Preliminary figure | This inspection |
| --- | --- |
| 2 workbooks | Confirmed |
| 12 worksheets | Confirmed |
| 667 candidate products | **639** model rows. The gap of 28 equals the Hilook section labels. Those labels must not be imported as products |
| 762 embedded images | Confirmed |
| 389 logged issues | Not reproducible. The issues file is not in the repository. Issue classes that do exist are documented above: missing descriptions, blank prices, `По запросу`, repeated models, stray cells, internal discount notes, non-photo-column anchors, shared merges, and images that do not sit on a product row |

## Limits of this inspection

- Anchor geometry says where a drawing starts and how far its `to` marker extends. It does not prove that a tall image was meant for every row it overlaps.
- Brand and the Hilook parent/child category tree are proposals.
- The price cells do not contain a currency code. USD is a confirmed business rule for those numbers, not a value read from the cell.
- Image pixel dimensions were not decoded; MIME type and byte size were.
- The inspection did not extract image files to disk. Extraction is an import-time job and must write new files, leaving both workbooks unchanged.
