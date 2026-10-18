# Catalog accuracy audit

Read-only comparison of the published catalog with `data/source/Hikvision pr.xlsx` and `data/source/Ezviz pr.xlsx` on 17 October 2026. The workbooks were opened and not saved. This inspection changed no product, category, price, description, image, or publication record. The later correction of findings F085 and F086 is recorded in that section.

Excel row numbers are worksheet rows. They are not column A and they are not `products.id`. Each published product was matched through its source record: source code, worksheet, and 1-based `source_row`.

## Executive summary

| Measure | Count |
| --- | ---: |
| Published products inspected | 639 |
| Drafts and archived products | 0 |
| Excel product and service rows | 639 |
| Source-to-catalog matches | 639 |
| Unmatched Excel product rows | 0 |
| Published products without a source record | 0 |
| Model text equal to the model cell, after the importer's whitespace collapse | 637 |
| Russian description equal to the description cell | 617 |
| Public price equal to the current price cell | 639 |
| Stored source price equal to the public price | 639 |
| Image set exactly equal to the drawings anchored on that model row | 476 |
| Structured specification rows | 0 |
| Approved exceptions checked | 9 products |
| Approved exceptions not applied | 0 |

Confirmed discrepancies are 49. Possible issues are grouped below and are not counted as confirmed mistakes. Those counts are the 17 October inspection. Findings F085 and F086 were corrected on 18 October 2026. The finding section keeps the original issue and records the public text checked after that correction.

| Category | Confirmed | Severity | Possible, not confirmed |
| --- | ---: | --- | --- |
| Model identifier | 1 | High | 0 |
| Description adds numbers the cell does not contain | 11 | High | 0 |
| Description changes the technical meaning | 1 | High | 1 wording difference whose numbers match |
| Missing image | 36 | Medium | 4 further gaps are the approved Seagate decision |
| Image set incomplete | 0 | — | 39 products keep one of several drawings on the row |
| Low-resolution or blurry image | 0 | — | 27 small files; dimensions were not stored and the files were not opened |
| Shared image | 0 | — | 84 checksums are used by more than one product |
| Price | 0 | — | 0 |
| Brand | 0 | — | 0 |
| Translation changed a measurement | 0 | — | 49 number-counter flags are thousands separators, spaced thousands, or an added `1U` / codec token |
| Missing Uzbek or English description | 8 | Medium | — |
| Uzbek or English title falls back to Russian | 614 | Low | Titles, not technical descriptions |

## How the comparison was made

The parser that the importer uses read both workbooks. It did not write them. Product and service rows supply the model, description, price kind and amount, brand text, section heading, and drawings whose anchor starts on that row and sits in the photo column. A drawing that only passes across a row is not treated as that row's photo.

The catalog side is the live database the public site reads: product, translations, source record, images, and category. Public prices were also checked against the stored source amount. All 639 stored amounts equal the public amounts. None of the 639 prices is locked. 587 public prices are numeric and 52 are on request.

A blank Excel price and an explicit "По запросу" price both map to public `on_request` with no amount. That mapping is the documented import rule, so those 52 rows are matches.

Model comparison uses the importer's display form, which collapses repeated spaces. `DS-2SE4C425MWG-E  14` in cell `C9` and `DS-2SE4C425MWG-E 14` in the catalog are the same model.

Category names that differ from a worksheet heading were counted, not raised as errors. The workbook's `другие устройства` sheet is a catch-all. The catalog has split 117 of those rows, plus some Hilook rows, into narrower published categories. That is an administrative assignment, not a cell mismatch.

No specification table is populated. Technical values live in the description prose, so this audit compared that prose with the description cell.

## Approved exceptions

Each exception was checked against the decision, not merely against the original cell. All nine match the decision.

| Product | Decision checked | Result |
| --- | --- | --- |
| 13–17 Seagate 500GB, 1TB, 2TB, 4TB, 6TB | Approved descriptions; no invented part numbers. HDD rows 12–16, cells `D12`–`D16` empty, prices `E12`–`E16` are 18, 56, 75, 135, 200 | Verified |
| 268 `DS-2SE4C425MWG-E 14` | `D9` keeps 15× optical and 16× digital. The `25x` title is not repeated | Verified |
| 494 `GDR-126035B` | Model is `GDR-126035B`. Catalog text does not say `GDR-126035BM`. Cell `D41` still contains `GDR-126035BM` | Verified |
| 528 `гибкий переход` | Approved three-language text. Category 38 `drugie-ustroystva` is published | Verified |
| 533 `12V 15A` | Catalog model is `12V 15A`. Cell `C80` remains `2V 15A`. The description keeps output `12V` and `15A` | Verified |

Products 13, 15, 16, and 17 have no catalog image. The workbook drawing on HDD rows 12–16 is one shared file, SHA-256 `5c230e2a0fd834e9fac25dc6c9ac367f226bb227a4c471cbc89fa2b9b7e16757`, and only product 14 carries it. That image gap is the approved choice, not a new mistake. It is listed with the image findings so the evidence stays visible.

## Confirmed source and catalog mismatches

### F113 — model, High

| Field | Value |
| --- | --- |
| Product | 549, catalog model `LOGA 5/1,8м` |
| Source | `Hikvision pr.xlsx`, sheet `другие устройства`, row 96, cell `C96` |
| Source value | `SWITTEX 1,8m` |
| Catalog value | `LOGA 5/1,8м` |
| Type | Confirmed source/catalog mismatch |
| Evidence | The source record points at row 96, and the model cell is `SWITTEX 1,8m`. Confidence: confirmed |
| Next action | Confirm with the client which model is sold. Do not choose one from the other cell |
| Client confirmation | Yes |

This is the only model mismatch among the 639 published products. Product 533 differs from `C80` because that difference was approved.

## Descriptions that add numbers the cell does not contain

These eleven description cells are empty. The published Russian text contains measurements, counts, or capacities. The numbers are not in the source cell, so they are unsupported claims. Confidence is confirmed for the mismatch. Whether a later datasheet justifies the wording is a client question. Do not pick a replacement number during a correction until that source is identified.

| ID | Product | Sheet, cell | Catalog text begins |
| --- | --- | --- | --- |
| F015 | 18 `DS-10HKVS-VX1 1TB` | HDD `D17` | `Жесткий диск Hikvision для видеонаблюдения DS-10HKVS-VX1, 1 ТБ.` |
| F085 | 433 `DS-K6B411TMX-M` | СКУД `D32` | At audit: glass swing barrier, about 30–40 people/min, opening about 0.2–0.5 s. Corrected 18 October 2026. |
| F086 | 434 `DS-K6B411TMX-R` | СКУД `D33` | At audit: the same 30–40 people/min and 0.2–0.5 s wording. Corrected 18 October 2026. |
| F087 | 437 `DS-K3B501SX-M/M` | СКУД `D36` | `12 пар ИК-детекторов` |
| F088 | 438 `DS-K3B501SX-R/M` | СКУД `D37` | `12 пар ИК-детекторов` |
| F089 | 441 `DS-K3B211LX-M` | СКУД `D40` | `4 пары ИК-датчиков` |
| F090 | 442 `DS-K3B211LX-L` | СКУД `D41` | `4 пары ИК-датчиков` |
| F091 | 447 `DRT-ES3216 Middle` | СКУД `D46` | `1400*160*980 мм`, 50 and 35 people/min |
| F092 | 448 `DRT-ES3216 Right` | СКУД `D47` | Same dimensions and the same 50 and 35 people/min |
| F094 | 451 `DS-TMG320-LR` | СКУД `D50` | Barrier series 32 text; the cell itself has no numbers |
| F095 | 453 `DS-TMG320-LR-B` | СКУД `D52` | Same barrier series 32 text |

Severity is High. Type is potentially unsupported claim, and also missing source information. Client confirmation is required before any of this text is kept or removed, except F085 and F086, which were corrected as recorded below. Product 18 also has a row drawing that is not attached; that image gap is counted with the missing images.

### F085 and F086 — corrected 18 October 2026

Original issue. СКУД `D32` and `D33` are empty. On 17 October the published Russian, Uzbek, and English descriptions for 433 `DS-K6B411TMX-M` and 434 `DS-K6B411TMX-R` said about 30–40 people per minute and about 0.2–0.5 seconds. Those two claims are not in the cells. The Excel cells were not changed.

Correction. Audit entry 1635 updated product 433, and audit entry 1636 updated product 434. Both are `product_updated` with `{"changes": ["translations"]}`. The two numerical claims were removed from Russian, Uzbek, and English. The official 5–60 second door-open duration was not inserted. Models, titles, prices, images, categories, slugs, and source records were not changed.

Current public descriptions. Both products now use this Russian text: `Стеклянный турникет (swing-барьер) премиум-класса. Корпус из нержавеющей стали, прозрачные створки. Бесщеточный мотор, плавное и тихое движение. Поддержка карт и распознавания лиц. Встроенные датчики безопасности и анти-tailgating. Аварийное автоматическое открытие при пожаре.` Uzbek: `Premium-klass shisha turniket (swing-to'siq). Zanglamaydigan po'lat korpus, shaffof qanotlar. Cho'tkasiz motor, ravon va tinch harakat. Kartalar va yuzni tanish qo'llab-quvvatlanadi. O'rnatilgan xavfsizlik datchiklari va anti-tailgating. Yong'inda avariya holatida avtomatik ochilish.` English: `Premium glass turnstile (swing barrier). Stainless-steel housing, transparent leaves. Brushless motor, smooth and quiet movement. Cards and face recognition are supported. Built-in safety sensors and anti-tailgating. Automatic emergency opening in a fire.` The public pages were checked in all three languages. `source_description_raw` still holds the pre-correction paragraph, including the two removed claims. The six translation rows are manually maintained and description-locked.

The Seagate rows are the same shape, an empty description cell, but their catalog paragraphs are the approved exception and are not in this list.

## Confirmed change of technical meaning

### F093 — description, High

| Field | Value |
| --- | --- |
| Product | 449 `DRT-Z-310` |
| Source | `Hikvision pr.xlsx`, sheet `СКУД`, row 48, cell `D48` |
| Source phrase | `Процент сдачи экзамена: 35 пенсов в месяц` |
| Catalog phrase | `Пропускная способность: 35 человек в минуту` |
| Rest of the paragraph | The surrounding measurements match, including `1,2/1,0 мм`, `200*200*980 мм`, 5 sensor pairs, passage `600-900 мм`, and input `100–240 В` |
| Type | Confirmed source/catalog mismatch. The number 35 is unchanged. The claim is not |
| Evidence | The source phrase is itself incoherent. The catalog replaces it with a throughput claim the cell does not make. Confidence: confirmed that the meaning changed; not confirmed that 35 people/min is the right specification |
| Next action | Restore the cell or obtain a source for the throughput sentence. Do not treat the catalog sentence as the workbook value |
| Client confirmation | Yes |

An automated number comparison marked this Low because 35 still occurs once. The meaning change is High.

## Possible wording difference

### F063 — description, Low, possible

Product 382 `IDS-TCM203-A`, sheet `Проектное оборудование`, row 14, cell `D14`. The first 220 characters of the source and the catalog are the same, including `1/1.8"`, `1920*1080`, `60fps/50fps`, and `8-32мм`. The full strings are not identical, and the difference is after that prefix. Extracted numbers match. This is not a confirmed numerical error. Client confirmation is not required until the later wording is reviewed.

## Images

Drawings were compared by SHA-256. A match means the stored file is the drawing anchored on that model row. It does not mean someone looked at the picture.

| Class | Count | How to read it |
| --- | ---: | --- |
| Confirmed correct image set | 476 | The stored checksum set equals the row's anchored drawings |
| Missing image | 40 | The row has an anchored drawing and the product has none. Four are the approved Seagate gaps, so 36 are new |
| Incomplete set | 39 | The stored checksum is one of the row's drawings. Another drawing on the same row is not stored. This is not a substituted wrong file |
| Shared checksum | 84 groups | The same file is attached to more than one product. A shared drawing is not automatically wrong |
| Small file | 27 | File size under 4,000 bytes, or width under 160 where width is known. Width and height are null for the sampled files, so blur was not judged |
| Association unclear | 0 | Every published product matched a source row, so no image was left without a row |

### Missing images by worksheet

| Sheet | Products with an anchored drawing and no catalog image |
| --- | ---: |
| другие устройства | 17 |
| HDD | 15, of which 4 are products 13, 15, 16, and 17 |
| Hilook | 4 |
| IP камеры | 2 |
| Домофоны | 1 |
| Проектное оборудование | 1 |

Examples of confirmed gaps, Medium, type "image mismatch or uncertainty":

| Product | Sheet, row | Evidence |
| --- | --- | --- |
| 3 `WD30PURX-78` | HDD row 2 | Anchored drawing `56ef1361…`, catalog has no image |
| 18 `DS-10HKVS-VX1 1TB` | HDD row 17 | Anchored drawing `daa444bf…`, catalog has no image |
| 13, 15, 16, 17 Seagate | HDD rows 12, 14, 15, 16 | Same drawing as product 14. Approved to stay without a separate photo |

Next action for the 36 non-approved gaps: attach the row's own drawing only after a person confirms it is that product's picture. Client confirmation is needed where several products share one drawing.

### Incomplete sets

All 39 High image flags from the checksum comparison are partial, not replacements. Example: product 22 `IPC-B149HA-LUF/SRB`, Hilook row 6, has two anchored drawings and stores one of them. The stored checksum is in the source set. Severity in this report is Medium, and the type is image uncertainty, not a confirmed wrong photo. The automated label "checksum does not match" overstated these 39 rows.

### Shared and small files

Eighty-four checksums belong to more than one product. The Seagate file and the PTZ drawing shared by products 267 and 268 are examples already documented. Identical files are recorded here as shared images that need verification only when a product should have had its own drawing.

Twenty-seven files are small. Examples include `IPC-B140HA` at 2,139 bytes, `THC-B129-LPS` at 2,001 bytes, and `Панель-заглушка` at 1,938 bytes. Stored width and height are null, and the files were not opened. They are possible low-resolution images, not confirmed blur.

## Prices

No price difference was found.

For every published product the public amount and status match the current workbook price cell: a numeric cell matches the public amount, and a blank or explicit on-request cell matches public on request with a null amount. The stored source amount equals that public amount on all 639 rows. No price is locked. There is no confirmed mismatch, no likely manual override, and no unclear price to review.

This comparison is against the workbooks as they are now. It cannot see a historical edit that was later changed back to the cell.

## Localization

Import does not fill Uzbek or English. Later editorial translations cover most descriptions.

Eight published products have neither an Uzbek nor an English description. Severity Medium. Type: missing information. The Russian description is what the public Uzbek and English pages fall back to.

| Product | Model |
| --- | --- |
| 186 | `DS-2CD2T87G2-L` |
| 398 | `DS-6908UDI` |
| 399 | `DS-6912UDI` |
| 454 | `DS-TMG520-L(6M)` |
| 638 | `7-дневная видеоистория событий` |
| 639 | `30-дневная видеоистория событий` |
| 640 | `7-дневная видеоистория событий` |
| 641 | `30-дневная видеоистория событий` |

Products 638–641 are service rows. The repeated Russian titles are the source names, not a failed translation of a model code. Client confirmation is needed only if these services should have distinct localized copy.

614 products have an empty Uzbek or English title, so the public page shows the Russian name with the existing fallback caption. That is a missing localized title. It is not, by itself, an incorrect technical description. Model identifiers are expected to stay unchanged across languages. Severity Low. No client confirmation is required to leave model codes as they are.

### Number flags in translations

A first pass flagged 49 Uzbek or English descriptions because a digit counter differed from the Russian text. Review of those counters shows they are not confirmed measurement changes:

- English and Uzbek write `5,200`, `10,400`, `4,600`, and `10,200` where Russian writes `5200`, `10400`, `4600`, and `10 200`. The values are the same.
- Russian `10 000` is split by the space. English writes `10000` or `10,000`.
- Several NVR translations add the form factor `1U` and the codec labels `H.265` / `H.264`. Those tokens add the digits 1, 265, and 264. They are extra words, not a changed voltage, resolution, or channel count. Example: products 243 `DS-7604NI-Q1`, 244 `DS-7608NI-Q1`, and 245 `DS-7616NI-Q1`.

No reviewed translation flag shows a source measurement replaced by a different measurement, such as 15× becoming 25× or 12V becoming another voltage. The 49 flags stay possible wording additions. They are not confirmed numerical errors. A correction pass should not rewrite them solely because the digit counter differed.

## Categories and visibility

All 639 products are published. Category 38 `drugie-ustroystva` is published and is the category of product 528, which matches the approved decision.

The 117 category moves off a worksheet heading are listed so a reviewer can see the assignment. They are not discrepancies.

| Worksheet heading | Catalog category | Products |
| --- | --- | ---: |
| другие устройства | Коммуникационные шкафы | 21 |
| другие устройства | СКУД | 19 |
| другие устройства | Кабели и разъёмы | 19 |
| другие устройства | Блоки питания | 13 |
| другие устройства | Монтажные принадлежности | 11 |
| Hilook | Коммутаторы HiLook | 10 |
| другие устройства | PoE-коммутаторы | 6 |
| Hilook | Домофоны HiLook | 5 |
| другие устройства | Комплектующие для шкафов | 5 |
| другие устройства | Источники бесперебойного питания | 3 |
| другие устройства | Сетевые фильтры | 3 |
| другие устройства | 4G-маршрутизаторы | 2 |

Brand text on the workbook row matches the catalog brand wherever both are present. No brand finding was produced. No option-label finding was produced.

## Limitations

- Images were compared by checksum and file size. They were not opened, so blur and a wrong-but-similar drawing cannot be confirmed visually.
- A drawing that spans several rows is excluded on purpose. Some of the 39 incomplete sets may be a second legitimate photo, and some may be a group drawing. The checksums do not decide which.
- The digit counter treats commas, spaces, and tokens such as `1U` and `H.265` as numbers. Those flags were reviewed and were not promoted to confirmed errors.
- Product 382 differs after the first 220 characters. The exact later words were not copied into this report.
- Structured specifications do not exist, so there is nothing to compare beside the description prose.
- Category publication was checked for the approved category and for the rule that a published product stays public. Every category page was not opened in a browser.
- The public site was not clicked product by product. The comparison used the database that the public API reads, including prices, translations, and image checksums.
- Prices match the workbooks as they stand today. An earlier manual price that was later returned to the cell would not appear.

## What this audit did not do

This audit inserted, updated, or deleted no catalog row. It changed no price, description, model, translation, image, category, or publication status. The workbooks were not saved. No migration ran. No test wrote to the catalog database. No service was rebuilt or restarted. Nothing was committed, pushed, or deployed. The later correction of F085 and F086 is recorded in that section and is not part of this 17 October inspection.
