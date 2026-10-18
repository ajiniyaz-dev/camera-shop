# Phase 1 — Catalog accuracy plan

Plan dated 17 October 2026, updated 18 October 2026. It reviews `docs/catalog-accuracy-audit.md`, `docs/catalog-accuracy-review.md`, `docs/unresolved-drafts.md`, and `docs/PROJECT_HANDOFF.md`. The catalog corrections applied from this plan are the description edit for products 433 and 434 and, later the same day, the client-approved text changes recorded in “Client-approved corrections.” Historical findings below are kept. Prices, images, categories, slugs, workbooks, and unrelated products were not changed.

The audit compared all 639 published products with the current workbooks. 639 source rows matched. Prices matched on all 639. This plan does not reopen that price comparison.

## How the checklist is counted

The audit’s 49 confirmed discrepancies are 11 unsupported descriptions, 1 model conflict, 1 changed specification sentence, and 36 missing images. Four further missing-image rows are the approved Seagate decision and are not part of those 36. Other audit records are possible issues or reviewed non-issues. A product can appear in more than one category. Each category is counted once.

This plan uses **22 checklist items**. Each item has one decision status. The 22 items cover every audit record below, including the grouped image and translation records.

| Status | Items | IDs |
| --- | ---: | --- |
| Completed | 5 | P1-02, P1-05, P1-07, P1-08, P1-17 |
| Safe to leave unchanged | 16 | P1-03, P1-04, P1-06, P1-09, P1-10, P1-11, P1-12, P1-13, P1-14, P1-15, P1-16, P1-18, P1-19, P1-20, P1-21, P1-22 |
| Needs client decision | 0 | |
| Needs further verification | 1 | P1-01 |
| Total reviewed | 22 | |

5 + 16 + 0 + 1 = 22. Phase 1A, on 18 October 2026, moved P1-02, P1-09, P1-11, P1-12, and P1-14 from further verification to ready, and moved P1-10 from a client decision to ready. Later the same day, P1-02 was applied. The client then answered P1-05, P1-07, P1-08, and P1-17, and those four decisions were applied. P1-05 required no text change: the existing ES3216 specifications were retained. The other sixteen ready items stay “safe to leave unchanged.” The original finding text is unchanged.

Approved exceptions stay as decided in `docs/unresolved-drafts.md`: products 13–17, 268, 494, 528, and 533. This plan does not reopen their wording, models, or image choices.

## A. Eleven descriptions whose Excel cells are empty

An empty `Характеристика` cell means the workbook does not support the claim. It does not prove the claim is false. Columns A–K, merged ranges, and comments were already checked in the review. The cells are empty. Manufacturer pages were checked for this plan. Direct requests to three `hikvision.com` product pages returned HTTP 500, so those quotes are the indexed text of the official URLs, not a second full-page render.

| Products | What the empty cell cannot decide | Independent evidence | Recommendation |
| --- | --- | --- | --- |
| 18 `DS-10HKVS-VX1 1TB` | `D17` is empty. `C17` is `DS-10HKVS-VX1     1TB`. | No datasheet for this exact model was found. An EU declaration lists `DS10HKVS-VX1`, without the hyphen and without `1TB`, as a digital video recorder. That string is not this cell. | Leave pending. Keep the model and the 1 TB token from `C17`. Do not treat “surveillance hard drive” as verified, and do not rewrite it as a recorder. |
| 433 `DS-K6B411TMX-M`, 434 `DS-K6B411TMX-R` | `D32` and `D33` are empty. Before the correction, both languages repeated `около 30–40 чел/мин` and `~0.2–0.5 сек`. | The official DS-K6B411TMX page indexes a brushless motor, door-open duration of 5 to 60 seconds, 6 dToF sensors, and MCBF of at least 5 million. It does not state 30–40 people per minute or a 0.2–0.5 second opening. Reseller pages do. A family brochure’s 20–60 people per minute belongs to other models. | Completed on 18 October 2026. Those two claims were removed. The 5–60 second duration was not inserted. The original finding is kept above. |
| 437 `DS-K3B501SX-M/M`, 438 `DS-K3B501SX-R/M` | `D36` and `D37` are empty. The claim is `12 пар ИК-детекторов` plus the permission, LED, pinch-alarm, self-check, passage-time, fire-alarm, and power-loss sentences. | A Hikvision datasheet for the DS-K3B501SX series states 12 IR pairs and the same feature list. The series user manual says the barrier has 12 IR lights and opens on a fire alarm. The datasheet’s model table shows `-L`, `-M`, and `-R`, not `-M/M` or `-R/M`. | Retain the feature text. Do not change the model suffix from this datasheet. |
| 441 `DS-K3B211LX-M`, 442 `DS-K3B211LX-L` | `D40` and `D41` are empty. The claim is `4 пары ИК-датчиков света` plus the LED, passage-time, and fire-alarm sentences. | The official DS-K3B211LX page states 4 pairs of IR light detectors, an LED passing direction, cancellation when the valid duration expires, and door wings left free when a fire alarm triggers. The word “glass” at the start of the catalog sentence is not in those bullets. | Retain the four verified sentences. Do not delete the paragraph because of the unverified word “glass”. |
| 447 `DRT-ES3216 Middle`, 448 `DRT-ES3216 Right` | `D46` and `D47` are empty. The claims are `1400*160*980 мм`, 50 and 35 people per minute, `1V2`, `-20℃~+70℃`, and `24 В 150 Вт`. | eSSL and a distributor ES3216 sheet use those dimensions, 50 people per minute open and 35 closed, 24 V 150 W, that temperature range, and the unusual `1V2` controller wording. No Hikvision page for `DRT-ES3216` was found. Middle and Right are not on those sheets. | Leave the text in place until the client accepts or rejects the ES3216 sheet as the authority for these two model strings. |
| 451 `DS-TMG320-LR`, 453 `DS-TMG320-LR-B` | `D50` and `D52` are empty. The claims are the series-32 description, a brushless DC motor, and a closing delay `от 1 до 600 секунд`. Product 453 adds the indicator-lamp sentence. | The official DS-TMG320 page states the same installation, motor, Bluetooth, chuck, and 1 to 600 second falling delay, and lists `DS-TMG320-LR` as the right-side body. The official `/B` page adds the indicator-light sentence and lists `DS-TMG320-LR/B`. The catalog model uses a hyphen in `DS-TMG320-LR-B`. | Retain both descriptions. Do not change the hyphen to a slash without a separate model decision. |

## B. Product 549 — `LOGA 5/1,8м` versus `SWITTEX 1,8m`

`Hikvision pr.xlsx`, sheet `другие устройства`, row 96:

- `C96` is `SWITTEX 1,8m`.
- `D96` is `Сетевой фильтр LOGA 5/1,8м с з/к с выключателем Цвет: Белый Производитель: LOGA Допустимый ток: 10 А Количество гнёзд: 5 Заземление: Да Наличие кнопки: Да Длина провода: 1,8м`.

The catalog display model and Russian title are `LOGA 5/1,8м`. The Russian description matches `D96`. The stored source model is still `SWITTEX 1,8m`. The public slug is still `product-swittex-1-8m`. Uzbek and English names are empty, so those titles fall back to `LOGA 5/1,8м`. Their descriptions follow `D96`.

Retail listings show a LOGA five-socket 1.8 m filter rated 10 A, with grounding and a switch. They also show a separate SVITTEX five-socket 1.8 m filter. `SWITTEX` is not established as either product. One LOGA listing is grey, while `D96` says white, so color does not choose between the two names.

The workbook itself disagrees. Retail pages show that both name families exist and do not say which unit is in this row. No model, brand, description, slug, or URL change is recommended.

## C. Product 449 — `DRT-Z-310`

`D48` and the published Russian description match except one sentence.

- Excel: `Процент сдачи экзамена: 35 пенсов в месяц`
- Russian catalog: `Пропускная способность: 35 человек в минуту`
- Uzbek: `O'tkazish qobiliyati: daqiqasiga 35 kishi.`
- English: `Pass rate: 35 persons per minute.`

The rest of `D48` is material `SUS304` at `1,2/1,0 мм`, size `200*200*980 мм`, 5 sensor pairs, passage `600-900 мм`, input `100–240 В`, a DC brush motor, environment `-20~+70`, supply `24 В 150 Вт`, and net weight `30 кг`. The stored source description still has the Excel sentence. The published text does not.

No Hikvision document for `DRT-Z-310` was found. A retailer specification for swing gate `X310` repeats that same block and labels the corresponding line `Pass rate: 35p/m`. That makes the people-per-minute reading consistent with the surrounding copied block, and it makes `пенсов в месяц` look like a damaged rendering of a pass rate. It does not certify `DRT-Z-310`.

Do not publish the literal Excel sentence as a specification. The three catalog languages agree with each other. They need a separate translation review only if the client rejects the pass-rate reading. Until then, leave all three sentences unchanged.

## Missing translations

These eight products have neither an Uzbek nor an English description. The audit localization table lists the same eight, in the same order: 186, 398, 399, 454, 638, 639, 640, and 641. The phrase “638–641” means those four service rows, not a different count. A missing translation is not evidence that the Russian specification is wrong. None of the eight is in the description-mismatch list, so this plan does not treat their Russian text as an accuracy defect.

| Product | Model | Recommendation |
| --- | --- | --- |
| 186 | `DS-2CD2T87G2-L` | Translate the existing Russian description. Do not add specifications. |
| 398 | `DS-6908UDI` | Same. This product also has an incomplete image set. |
| 399 | `DS-6912UDI` | Same. This product also has an incomplete image set. |
| 454 | `DS-TMG520-L(6M)` | Translate the existing Russian description. Do not import numbers from the DS-TMG320 pages. |
| 638 | `7-дневная видеоистория событий` | Translate this service row from its own Russian text. Do not merge it with 640. |
| 639 | `30-дневная видеоистория событий` | Translate this service row from its own Russian text. Do not merge it with 641. |
| 640 | `7-дневная видеоистория событий` | Keep it as a separate source row. Translate only its own text. |
| 641 | `30-дневная видеоистория событий` | Keep it as a separate source row. Translate only its own text. |

614 products have an empty Uzbek or English title, so the public page shows the Russian name and the existing fallback caption. Model codes are expected to stay unchanged. This is not a specification defect. Leaving those titles untranslated is the recommended action. Adding marketing names would be a separate content project.

Forty-nine Uzbek or English descriptions differed from Russian only in a digit counter. The review showed thousands separators (`5200` and `5,200`), spaced thousands (`10 200`), and added tokens such as `1U` and `H.265`. No reviewed flag replaced one measurement with another. Do not rewrite those descriptions because the counter differed.

## Missing images

Forty products have at least one drawing anchored on the model row and no catalog image. The association rule used here is the importer’s high-confidence rule: the drawing’s anchor starts on that model row and sits in the photo column. A drawing that only spans a row is not a product photo. File size is not evidence that a picture is blurry or wrong. Phase 1A later opened the unverified drawings; the results are in that section. The paragraph below is the original inventory.

### Preserve the approved Seagate gaps

Products 13, 15, 16, and 17 share SHA-256 `5c230e2a…` with product 14, which already stores it. The approved decision was not to attach that one drawing to the other capacities. Do not attach it.

### Shared drawings, not one photo per product

These rows have a drawing, and the same file is anchored on more than one model. Attaching it to every row would repeat the Seagate situation without an approval.

| Drawing | Products with no image |
| --- | --- |
| `56ef1361…` | 3 `WD30PURX-78`, 4 `WD40PURX-78` |
| `75b64d44…` | 5 `WD60PURX-78`, 6 `WD80PURX-78`, 7 `WD102PURX-78` |
| `daa444bf…` | 8 `DS-20HKVS-VXI`, 9 `DS-40HKVS-VXI`, 10 `DS-60HKVS-VXI`, 11 `DS80HKVS‐VX1`, 12 `DS120HKAI-VX1`, 18 `DS-10HKVS-VX1 1TB` |
| `7ca0d559…` | 110 `DS-KIS202T`, 111 `VDP-K203` |
| `386a0f08…` | 458 `Andel Q788`, 459 `Cougar Q799` |
| `aa2a77f6…` | 462 `Замок 180кг`, 463 `Замок 280кг`, 464 `Замок 350кг` |
| `4273e7c0…` | 478 `Кронштейн 30SMX60SM M-901`, 480 `Кронштейн 60SMX120SM M-901` |
| `e1bb7d45…` | 554 `SMART-16-POE`, 555 `SMART-16-POE Gigabit` |
| `900cd35f…` | 556 `SMART-24-POE`, 557 `SMART-24-POE Gigabit` |

Product 554 also has a second drawing, `fe3146fb…`, that is not on product 555. Do not attach either file until the pair is identified.

### One drawing on one model row

These nine products have a single anchored drawing that is not shared with another imageless row: 37 `IPC-B160HA-LUF/SL`, 184 `DS-2CD2T83G2-4LI2U 4MM Black`, 200 `DS-2CD2687G3-LIZS2UY/SL`, 383 `IDS-TCM403-B`, 481 `M002`, 522 `BNC`, 524 `RG-45 connector CAT6`, 525 `RG-45 CAT6 connector Metall`, and 548 `4G R611C`. The anchor evidence is sufficient to identify the file. The picture was not opened, so attachment waits until someone looks at that file.

### Association not clean enough to attach

- Product 25 `IPC-B429H (С)`, Hilook row 9, is anchored to `26b0863c…`. That is the same checksum previously identified as the drawing spanning PTZ rows 4–9, which is not the PTZ product image. Do not attach it on the anchor alone.
- Product 289 `DS-KIS611-S` has three different anchored drawings and no catalog image. The checksums do not say which one is the product.
- Product 489 `DS-1280ZJ-XS` has 21 anchored drawings, including one repeated checksum. This is a pile of files on one accessory row, not one confirmed photo.

### Incomplete sets

Thirty-nine products already store one drawing from the row and lack at least one other anchored drawing. The stored file is one of the row’s drawings, not a substituted file. Do not add or remove files until the extra drawing is opened. The products are 22, 23, 24, 26, 29, 63, 71, 72, 149, 163, 172, 210, 231, 237, 239, 240, 247, 263, 276, 278, 288, 290, 366, 367, 389, 394, 395, 398, 399, 400, 401, 402, 455, 552, 553, 563, 568, 591, and 606. Products 398 and 399 are also in the missing-translation list. Those are two separate actions.

### Already stored shared files, and small files

Eighty-four checksums are used by more than one product. A shared file is not an error. Products 267 and 268 share the approved PTZ drawing. Do not split those groups.

Twenty-seven stored files are under 4,000 bytes, and their pixel dimensions were not stored. That is not a finding that they are blurry. Product 528’s approved row-75 image is in this size group and stays. Product 549’s small file is not evidence about the LOGA/SWITTEX name.

## Action matrix

| Finding ID | Product ID and model | Issue category | Exact source evidence | Current catalog value | Recommended action | Evidence or verification source | Confidence | Decision status | Expected affected fields and languages |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1-01 / audit F015 | 18 `DS-10HKVS-VX1 1TB` | Unsupported description | HDD `D17` empty. `C17` is `DS-10HKVS-VX1     1TB`. | ru/uz/en call it a surveillance hard drive of 1 TB. | Leave the sentence pending. Keep the model capacity. Do not relabel it as a recorder. Do not attach the shared row drawing. | Phase 1A: the exact model is absent from Hikvision’s 22 November 2024 HDD compatibility list. The row drawing is a Toshiba 1TB label, not a Hikvision label. | Low | Needs further verification | `description` ru, uz, en. Not the model. No image. |
| P1-02 / audit F085, F086 | 433 `DS-K6B411TMX-M`; 434 `DS-K6B411TMX-R` | Unsupported numerical claim | СКУД `D32` and `D33` empty. | Before the correction: `30–40` people/min and `0.2–0.5` s in ru, uz, and en. | Remove those two numerical claims in ru, uz, and en. Do not replace them with the official 5–60 second door-open duration, which is a different parameter. | Completed 18 October 2026. See the completed-correction section. The official page does not state either number. | High | Completed | `description` ru, uz, and en. Applied. No other field. |
| P1-03 / audit F087, F088 | 437 `DS-K3B501SX-M/M`; 438 `DS-K3B501SX-R/M` | Description absent from Excel, present in a series datasheet | СКУД `D36` and `D37` empty. | 12 IR pairs and the series feature paragraph in ru, uz, and en. | Retain the feature text. Do not change `-M/M` or `-R/M`. | Hikvision DS-K3B501SX datasheet and series user manual, including “12 IR lights”. | High | Safe to leave unchanged | No edit if retention is approved. |
| P1-04 / audit F089, F090 | 441 `DS-K3B211LX-M`; 442 `DS-K3B211LX-L` | Description absent from Excel, present on the official page | СКУД `D40` and `D41` empty. | 4 IR pairs and the LED, duration, and fire-alarm sentences. “Glass” is extra. | Retain the paragraph. | Indexed official DS-K3B211LX page. Live fetch returned HTTP 500. | Medium | Safe to leave unchanged | No edit if retention is approved. |
| P1-05 / audit F091, F092 | 447 `DRT-ES3216 Middle`; 448 `DRT-ES3216 Right` | Unsupported in Excel; third-party sheet matches | СКУД `D46` and `D47` empty. | At the review: dimensions, 50 and 35 people/min, `1V2`, temperature, and `24 В 150 Вт`. Those specifications are still the public text. | The client accepted the existing ES3216 specifications for both products. No description was rewritten. | eSSL SB-ES-3216 and an ES3216 datasheet using the same `1V2` wording. Not a Hikvision page. Client confirmation, 18 October 2026. | Medium | Completed | No field. The approved specifications stay in ru, uz, and en. |
| P1-06 / audit F094, F095 | 451 `DS-TMG320-LR`; 453 `DS-TMG320-LR-B` | Description absent from Excel, present on the official page | СКУД `D50` and `D52` empty. | Series description, 1 to 600 seconds, and, on 453, indicator lamps. | Retain both descriptions. Do not change the model hyphen. | Indexed official DS-TMG320 and DS-TMG320/B pages. Live fetch returned HTTP 500. | Medium | Safe to leave unchanged | No edit if retention is approved. |
| P1-07 / audit F113 | 549, formerly displayed as `LOGA 5/1,8м` | Conflicting model identifier | `C96` `SWITTEX 1,8m`. `D96` names LOGA 5/1,8м and matches the description that was public at the review. | At the review: display model `LOGA 5/1,8м`. Source model and slug `product-swittex-1-8m` already said SWITTEX. Applied: display model and ru/uz/en titles `SWITTEX 1,8m`; public description `SWITTEX 1,8m.` The LOGA specification was not kept. | The client confirmed the sold name is SWITTEX 1.8 m, not LOGA. The LOGA description was not verified for SWITTEX, so it was replaced with that neutral sentence. | Workbook cells, catalog record, and the client confirmation of 18 October 2026. | Low | Completed | `model_display`, and `localized_name` plus `description` in ru, uz, and en. Slug unchanged. The admin save also set `model_raw`, `model_normalized`, and `model_locked`. |
| P1-08 / audit F093 | 449 `DRT-Z-310` | Description changes the source sentence | `D48`: `35 пенсов в месяц`. The other measurements match. | At the review: ru/uz/en said 35 people per minute. Applied: `35 пенсов в месяц`, `Oyiga 35 pens.`, and `35 pence per month.` The other measurements stay. | The client confirmed the source wording and the meaning 35 pence per month. The people-per-minute claim was replaced. The garbled Excel label was not published as the meaning. | `D48` and the client confirmation of 18 October 2026. | Low | Completed | `description` ru, uz, and en. No other field. |
| P1-09 / audit F063 | 382 `IDS-TCM203-A` | Unit at the end of the description | `Проектное оборудование` `D14` ends `850 мм`. The rest of the cell matches. | Russian ends `850 nm`. Uzbek and English also say `850 nm`. | Keep `850 nm`. Do not restore `мм`. | Phase 1A: the only difference is those two characters. The Hikvision datasheet for `iDS-TCM203-A` says `850 nm`. Status changed from further verification to ready. | High | Safe to leave unchanged | No edit. The catalog unit already matches the datasheet. |
| P1-10 / audit F001–F010, F016, F027, F028, F100–F107, F116–F119 | Shared missing drawings listed above, including product 18’s image | Missing image whose file is shared by several models | One photo-column drawing per row, same checksum on the sibling rows. | No image, so the public page uses the placeholder. | Do not attach these shared drawings. The opened files contradict using one picture for every listed model. | Phase 1A visual check. Status changed from client decision to ready. | High | Safe to leave unchanged | No image edit. |
| P1-11 / audit F023, F032, F033, F064, F107, F109–F112 | 37, 184, 200, 383, 481, 522, 524, 525, 548 | Missing image with one unshared row drawing | The files were opened. Several also sit on a neighboring row, and the others do not show the model text. | No catalog image. | Do not attach these files. Product 524’s jar photo is the only plausible small picture, and it stays off until a separate quality decision. | Phase 1A visual check. Status changed from further verification to ready. | High | Safe to leave unchanged | No image edit. |
| P1-12 / audit F020, F058, F108 | 25 `IPC-B429H (С)`; 289 `DS-KIS611-S`; 489 `DS-1280ZJ-XS` | Image association unclear | Row 9 is a ColorVu logo. Row 10 has three different intercom pictures with no model number. Row 36’s 21 files include a cable reel and span later rows. | No catalog image. | Do not attach these sets. | Phase 1A visual check. Status changed from further verification to ready. | High | Safe to leave unchanged | No image edit. |
| P1-13 / audit F011–F014 | 13, 15, 16, 17 Seagate | Approved missing image | HDD rows 12 and 14–16 share `5c230e2a…` with product 14. | Placeholder. Product 14 keeps the file. | Leave them without that image. | `docs/unresolved-drafts.md`. | High | Safe to leave unchanged | No image edit. |
| P1-14 / audit partial-image IDs F017–F038, F045, F054–F057, F059, F061, F062, F067–F074, F097, F114, F115, F120, F121, F127, F130 | 39 products listed in the incomplete-set section | Stored image set is a subset of the row | The stored checksum is one of the row’s drawings. The missing file is usually the ColorVu logo or a “NEW” badge. | The product photo already stored. The logo and badge are not stored. | Do not add the extra drawings. | Phase 1A visual check of every extra checksum. Status changed from further verification to ready. | High | Safe to leave unchanged | No image edit. |
| P1-15 | 84 checksum groups, including 267 and 268 | Shared image already stored | Identical checksums on more than one product. | The shared file is already attached. | Do not split or replace a shared file merely because it is shared. | Audit shared-image count. Approved PTZ pair in `docs/unresolved-drafts.md`. | High | Safe to leave unchanged | No image edit. |
| P1-16 | 27 files, including two on product 519 and the approved image on 528 | Small file, not a judged picture | Byte size under 4,000. Width and height were null. | Those stored files. | Do not mark them blurry or replace them because of size. | Audit file-size sample. Files were not opened. | Low | Safe to leave unchanged | No image edit. |
| P1-17 | 186, 398, 399, 454, 638, 639, 640, 641 | Missing Uzbek and English descriptions | Import does not fill uz/en. At the review these eight had neither description. | Russian descriptions for 186, 398, 399, and 454 were kept. Uzbek and English descriptions were added. Services 638–641 received a short description in all three languages. | The client approved translations of the existing descriptions, and short service descriptions drawn only from each row’s title, service kind, and billing period. | Audit localization table and the client confirmation of 18 October 2026. Products 398 and 399 overlap P1-14 only; their images were not changed. | High | Completed | `description` uz and en for 186, 398, 399, and 454. `description` ru, uz, and en for 638–641. Russian equipment text unchanged. |
| P1-18 | 614 products | Uzbek or English title falls back to Russian | `localized_name` is empty. | Russian model or name, with the fallback caption. | Leave model-code titles untranslated. | Audit count. Public fallback is specified in `docs/PROJECT_HANDOFF.md`. | High | Safe to leave unchanged | No title edit. |
| P1-19 | 49 translation rows, including 243, 244, and 245 | Digit counter differed | Russian and the translation use different grouping or an added `1U` / codec token. | The measurements that were reviewed still match. | Do not rewrite these translations for the counter alone. | Audit translation review. | High | Safe to leave unchanged | No description edit. |
| P1-20 | 13–17, 268, 494, 528, 533 | Approved exception | See `docs/unresolved-drafts.md`. | Matches the approved decision, as checked in the audit. | Do not alter these exceptions. | Audit exception check, nine products, all verified. | High | Safe to leave unchanged | No field. |
| P1-21 | All 639 published products | Price | Current price cells, including blank and explicit on-request cells. | Public amount and stored source amount match. None is locked. | Do not change prices. | Audit price section. | High | Safe to leave unchanged | No price field. |
| P1-22 | 117 products moved off a worksheet heading | Category label | Worksheet headings such as `другие устройства` and `Hilook`. | Narrower published categories listed in the audit. | Do not treat the heading difference as an error. | Audit category table. Category 38 remains the approved home of product 528. | High | Safe to leave unchanged | No category edit. |

## Corrections that can be approved from the current evidence

These approvals do not by themselves change the database. They approve a decision.

- Retain the descriptions of products 437, 438, 441, 442, 451, and 453. The empty Excel cells remain empty. The claims that were checked match Hikvision series documentation.
- Keep product 382’s `850 nm`. The Excel cell says `850 мм`, and the Hikvision datasheet says `850 nm`.
- Leave products 13, 15, 16, and 17 without the shared Seagate drawing.
- Leave every drawing reviewed in Phase 1A unattached. That includes the shared hard-drive labels, the ColorVu logo, the “NEW” badge, and the 21-file set on product 489. Product 524’s small jar photo stays off; accepting it would be a later quality choice, not an open accuracy defect.
- Leave the 84 already-shared images, the 27 small files, the 614 untranslated model titles, the 49 digit-counter translations, all 639 prices, and the 117 category assignments unchanged.
- Leave the nine approved-exception products unchanged.

The removal for products 433 and 434 is no longer in this list. It is recorded as completed below.

## Completed correction — products 433 and 434

Completed on 18 October 2026. This record does not call for the edit to be repeated.

Products 433 `DS-K6B411TMX-M` and 434 `DS-K6B411TMX-R` no longer say that they handle 30–40 people per minute or that they open in about 0.2–0.5 seconds. Those two sentences were removed from the Russian, Uzbek, and English descriptions. The official 5–60 second door-open duration was not written in their place. The remaining sentences, including the brushless motor, cards and face recognition, anti-tailgating, and fire opening, were kept.

Unchanged on both products: model, title, price, images, category, slug, and source record. The six translation rows are manually maintained and description-locked. `source_description_raw` still contains the paragraph from before the correction, including the two removed claims. It does not match the empty Excel cells `D32` and `D33`, and it no longer matches the published descriptions.

Audit entries 1635 and 1636 record `product_updated` with `{"changes": ["translations"]}` for products 433 and 434. `api/tests/test_catalog_admin.py` was run on a disposable database: 8 passed, with one `StarletteDeprecationWarning` for httpx. The public pages were checked in Russian, Uzbek, and English. The published count remained 639.

## Client-approved corrections — 18 October 2026

The client answered the four questions in `docs/phase-1-client-decisions.md`. The answers were applied through the admin product update. No SQL update, workbook edit, import, or price replacement was used. Products 447 and 448 were not saved again because their Russian, Uzbek, and English descriptions already contained the approved specifications.

**Product 549.** The client confirmed the name SWITTEX 1.8 m, not LOGA. `model_display` is `SWITTEX 1,8m`. The Russian, Uzbek, and English titles are `SWITTEX 1,8m`. The public description in all three languages is `SWITTEX 1,8m.` The previous LOGA description, including sockets, 10 A, color, grounding, and the manufacturer name, is no longer public because it was not verified for SWITTEX. The slug remains `product-swittex-1-8m`. Price `2.80` USD, brand, category 46, and the image are unchanged. The admin save also set `model_raw` and `model_normalized` to the new name and set `model_locked`. `source_description_raw` still begins with the LOGA paragraph. That source copy is history, not the public description.

**Product 449.** The client confirmed `35 пенсов в месяц` and the meaning 35 pence per month. Russian now says `35 пенсов в месяц`, Uzbek `Oyiga 35 pens.`, and English `35 pence per month.` The people-per-minute sentence is gone. The other measurements remain. Model, price `500.00` USD, image, category, and slug are unchanged. `source_description_raw` still contains the workbook sentence, including `35 пенсов в месяц`. `model_raw` still has its trailing space and was not rewritten.

**Products 447 and 448.** The client approved the existing ES3216 specifications. Both descriptions still include `1400*160*980`, 50 people per minute during working hours, 35 people per minute during ordinary closing, `1V2`, RGB, `-20℃~+70℃`, and `24 V 150 W` in Russian, Uzbek, and English. No new specification was added. Models, prices `800.00` and `580.00` USD, images, categories, and slugs are unchanged.

**Products 186, 398, 399, and 454.** The existing Russian descriptions were translated into Uzbek and English. The Russian text was not edited. The truncated Russian word `глубок` on product 186 was translated as deep learning / `chuqur o'rganish`, which is the sense of that sentence together with AcuSense. No measurement was added. Prices, models, images, categories, and slugs are unchanged. Products 398 and 399 remain on request.

**Products 638, 639, 640, and 641.** Each row is a service. The descriptions name the 7-day or 30-day video event history and the billing period already stored on the row: monthly for 638 and 639, yearly for 640 and 641. They are not described as equipment. Titles, models, prices (`3.00`, `5.00`, `30.00`, `50.00` USD), option labels, categories, and slugs are unchanged.

Changed translation rows are description-locked and have origin `manual`. Russian rows whose description text did not change stayed origin `source` and unlocked: 186, 398, 399, and 454. Identity checks after the last save showed slugs, prices, brands, categories, option labels, source records, image counts, and the other products’ display models unchanged. The published count stayed 639.

`api/tests/test_catalog_admin.py` was run again on a new disposable database: 8 passed, with one `StarletteDeprecationWarning` for httpx. The disposable database was removed afterward. Public product JSON was read for all twelve products in Russian, Uzbek, and English. The rendered pages were opened for 549 in all three languages, 449 in all three languages, 447 in Russian, 186 and 454 in English, 398 in Uzbek, 638 in Russian, and 640 in English.

## Decisions Required

The four client questions below were answered and applied on 18 October 2026. The original questions are kept so the evidence is not lost. One finding can still be settled from manufacturer documentation. Do not ask anyone to guess a product type. The shared-drawing question is not in this list: Phase 1A showed that those files are not one photo for every sibling.

### Client confirmation

**Which name is sold as product 549?** Answered: the unit is `SWITTEX 1,8m`. Applied the same day. The question and evidence below are the record from before that answer.

- Products: 549. Display model `LOGA 5/1,8м`. Source model `SWITTEX 1,8m`.
- Evidence: `другие устройства` `C96` is `SWITTEX 1,8m`. `D96` describes `LOGA 5/1,8м`, a white five-socket 1.8 m filter, 10 A, with grounding and a switch. The Russian description matches `D96`. The slug is `product-swittex-1-8m`. Retail pages show both a LOGA filter and a SVITTEX filter, and one LOGA listing is grey rather than white. Neither page identifies this row.
- Before the answer: do not change the model, brand, description, slug, or URL. That wait ended when the client confirmed `SWITTEX 1,8m`.

**May the pass-rate sentence stay on product 449?** Answered: the meaning is 35 pence per month, from `35 пенсов в месяц`. Applied the same day. The question and evidence below are the record from before that answer.

- Product: 449 `DRT-Z-310`.
- Evidence: `D48` says `35 пенсов в месяц`. Russian says `35 человек в минуту`, Uzbek says `daqiqasiga 35 kishi`, and English says `35 persons per minute`. The other measurements match `D48`. No Hikvision document for `DRT-Z-310` was found. A retailer block for swing gate `X310` labels the same line `35p/m`. That parallel is not a `DRT-Z-310` document.
- Before the answer: leave all three sentences as they are. Do not publish `35 пенсов в месяц`, and do not choose the people-per-minute reading as verified. That wait ended when the client confirmed 35 pence per month.

**Does the ES3216 sheet apply to products 447 and 448?** Answered: yes, the existing specifications stay. No text was rewritten. The question and evidence below are the record from before that answer.

- Products: 447 `DRT-ES3216 Middle` and 448 `DRT-ES3216 Right`.
- Evidence: `D46` and `D47` are empty. The catalog states `1400*160*980 мм`, 50 and 35 people per minute, `1V2`, `-20℃~+70℃`, and `24 В 150 Вт`. An eSSL sheet and a distributor ES3216 sheet use those figures, including the unusual `1V2` wording. No Hikvision page for `DRT-ES3216` was found. Middle and Right are not on those sheets.
- Before the answer: leave the descriptions unchanged. Do not treat the third-party sheet as accepted, and do not delete the claims. That wait ended when the client accepted the existing specifications.

**Should Uzbek and English descriptions be commissioned for these eight products?** Answered: yes. The four equipment descriptions were translated, and the four services received short descriptions in Russian, Uzbek, and English. Applied the same day. The question and evidence below are the record from before that answer.

- Products: 186 `DS-2CD2T87G2-L`, 398 `DS-6908UDI`, 399 `DS-6912UDI`, 454 `DS-TMG520-L(6M)`, 638 `7-дневная видеоистория событий`, 639 `30-дневная видеоистория событий`, 640 `7-дневная видеоистория событий`, and 641 `30-дневная видеоистория событий`.
- Evidence: the audit and this plan list the same eight. Each has a Russian description and no Uzbek or English description. The public pages fall back to Russian. Products 638 and 640 share one service name, and 639 and 641 share the other. Those are separate source rows. Products 398 and 399 also lack a second workbook drawing; that image question is already closed under P1-14 and is not part of this translation decision.
- Before the answer: do not write translations, do not merge the repeated service names, and do not add specifications. That wait ended when the client approved the translations and the short service descriptions.

### Further authoritative research

**What device is product 18?**

- Product: 18 `DS-10HKVS-VX1 1TB`.
- Evidence: HDD `C17` is `DS-10HKVS-VX1     1TB` and `D17` is empty. The catalog calls it a surveillance hard drive in all three languages. Hikvision’s 22 November 2024 HDD compatibility list includes `DS20HKVS-VX1`, `DS40HKVS-VX1`, and `DS60HKVS-VX1`, and does not include `DS-10HKVS-VX1`. No official datasheet for that exact string was found. An EU declaration uses the different string `DS10HKVS-VX1` for a recorder, so it does not reclassify this row. The shared drawing is a Toshiba 1TB label, not this model.
- While waiting: leave the description and the missing image unchanged. Do not infer a hard drive or a recorder, and do not attach the Toshiba drawing. This is not a client question until an authoritative document is found or the search is exhausted.

## Claims that were not independently verified

- Product 18 is a surveillance hard drive. The capacity token is in `C17`. The exact model is not in the official HDD list that was checked, and the row drawing is a Toshiba 1TB label.
- Products 447 and 448 were later accepted by the client. The ES3216 figures stay. They were not independently verified as a Hikvision document.
- Product 449’s people-per-minute sentence was the catalog text at the review. The client later replaced it with 35 pence per month. The `X310` parallel is still not a `DRT-Z-310` document.
- Which of `C96` and `D96` identifies product 549 was later answered by the client: `SWITTEX 1,8m`. The LOGA paragraph remains only in `source_description_raw`.
- The word “glass” on products 441 and 442.
- The 27 small files that were already stored were not opened again. Phase 1A opened the unverified missing and extra drawings.
- The exact suffix difference between catalog `DS-K3B501SX-M/M` and `DS-K3B501SX-R/M` and the datasheet’s `-M` and `-R`. The feature text can still be retained.
- The hyphen in `DS-TMG320-LR-B` versus the official `DS-TMG320-LR/B`. The description can still be retained.

## Implementation order

1. Leave the sixteen no-edit items unchanged. Do not repeat the completed removal on products 433 and 434.
2. The four client decisions in `Decisions Required` were obtained and applied on 18 October 2026. Do not apply a further name, pass-rate, or translation change without a new decision.
3. Leave product 18 unchanged until an authoritative document for the exact model `DS-10HKVS-VX1` is found. Do not use the Toshiba label as its photo.
4. After a later decision, apply accepted text changes through the admin API, not by SQL and not by re-importing the workbook. An Excel re-apply would see the empty description cells. For products 437, 438, 441, 442, 447, 448, 451, and 453, `source_description_raw` copies the catalog paragraph and does not match the empty cell. For products 433 and 434 it still copies the pre-correction paragraph, so it matches neither the empty cell nor the published text. Accepting Excel on a later import would clear those descriptions.
5. When a Russian description changes, change the Uzbek and English descriptions in the same edit so a removed number does not survive in another language.
6. Do not change slugs. Product 549’s public URL stays `product-swittex-1-8m` until a redirect policy exists. `slug_redirects` is not in the schema.
7. Do not rebuild or restart the running API as part of the data correction. The public site reads the database directly.

## Validation plan

Use a disposable database. The existing API tests create and drop their own database when `PHASE2A_ADMIN_URL` points at a temporary PostgreSQL. They must not use the Compose catalog. Do not run a migration for this work. The corrections are data edits, not schema changes.

Database integrity after a later, approved edit:

- Published count stays 639 unless a decision says otherwise. No product is archived, unpublished, or deleted.
- Products 13–17, 268, 494, 528, and 533 still match the approved text, prices, and image choices.
- A retained description still matches the approved paragraph in ru, uz, and en.
- A removed claim is absent from all three locales.
- Product 549’s slug remains `product-swittex-1-8m` unless a redirect is designed first.
- Prices, locks, brands, and categories for untouched products stay unchanged.
- No Phase 1A image is attached. Product 489 does not receive its 21 files, and product 18 does not receive the Toshiba label.
- `source_description_raw` is either left as provenance or explicitly updated. It must not be mistaken for the Excel cell on the ten products where it already differs.

Public catalog:

- The edited product’s ru, uz, and en pages show the approved text.
- A product with no Uzbek or English description still shows the Russian-original caption, and the caption disappears only where a real translation was saved.
- A product with no image still shows the existing placeholder.
- A newly attached image is the primary public image and is served from the public media path.
- Category 38 still lists product 528, and the Seagate products still show the approved placeholders except product 14.

Regression tests, on the disposable database only:

- `api/tests/test_public_catalog.py` for publication, locale fallback, and image visibility.
- `api/tests/test_catalog_admin.py` for an authenticated description and image update.
- `api/tests/test_price_labels.py` so an edit does not disturb on-request labels.
- `npm run typecheck` in `web/` if a test or fixture string changes. No production build or deploy is part of the data correction.

## Phase 1A investigation — 18 October 2026

This pass re-checked the items that were still unverified. The workbooks were opened and not saved. The drawings were extracted and looked at. No catalog field was changed.

### Product 18 — `DS-10HKVS-VX1 1TB`

Source: `Hikvision pr.xlsx`, HDD row 17. `C17` is `DS-10HKVS-VX1     1TB`. `D17` is empty. The catalog says, in all three languages, that it is a Hikvision surveillance hard drive of 1 TB.

Hikvision’s HDD compatibility list dated 22 November 2024, published on hikvision.com, lists `DS20HKVS-VX1`, `DS40HKVS-VX1`, and `DS60HKVS-VX1` as surveillance drives. It does not list `DS-10HKVS-VX1`. No official datasheet for that exact string was found. A reseller page uses the exact string and calls it a 1TB surveillance drive, but the same page also mixes in other model numbers, so it is not accepted as manufacturer documentation. An EU declaration names `DS10HKVS-VX1`, without the hyphen and without `1TB`, as a digital video recorder. That is a different string, and the same declaration groups it with models the HDD list treats as drives, so it is not used to reclassify this row.

The drawing on HDD rows 7–11 and 17 is one 147×147 file. It shows a Toshiba hard-disk label marked 1TB. It does not show `DS-10HKVS-VX1`. It is the same file for the 2TB, 4TB, 6TB, 8TB, and 12TB rows.

Confirmed: the model cell contains `1TB`, and the description cell does not. Uncertain: whether the exact model is a surveillance hard drive. Recommended action: leave the description and the missing image unchanged. Do not attach the Toshiba label.

### Products 433 and 434

Source: СКУД `D32` and `D33` are empty. Models are `DS-K6B411TMX-M` and `DS-K6B411TMX-R`. At the time of this investigation, all three languages said about 30–40 people per minute and about 0.2–0.5 seconds.

The official DS-K6B411TMX page lists both models. Its specification block states a brushless motor, MCBF of at least 5 million, door-open duration of 5 to 60 seconds, and 6 dToF sensors. It does not state 30–40 people per minute or a 0.2–0.5 second opening time. The 5–60 second value is how long the door remains open, not how fast the leaf moves. Face-recognition duration below 200 ms is also a different measurement. The TX-series user manual says opening speed can be configured and does not give 0.2–0.5 seconds.

Confirmed: those two catalog numbers are not in the official specification that was read. The removal was later applied and is recorded in the completed-correction section. The 5–60 second duration was not written into the sentence.

### Product 382 — `IDS-TCM203-A`

Source: `Проектное оборудование` row 14, `C14` `IDS-TCM203-A`, `D14` the full cell. The cell and the Russian description are both 276 characters. They match except the last two characters: the cell ends `850 мм` and the catalog ends `850 nm`. Uzbek and English also say `850 nm`. The earlier characters, including `1/1.8"`, `1920*1080`, `60fps/50fps`, and `8-32мм`, match. The cell’s typo `подсвктка` is still in the Russian text.

The Hikvision datasheet `iDS-TCM203-A_20210123Europe.pdf` states “IR illuminator 850nm” and “850 nm IR wavelength” for the 8–32 mm lens variant. Confirmed: the catalog unit matches that datasheet, and the Excel unit does not. Recommended action: keep `850 nm`. Do not restore millimeters, and do not add the datasheet’s 100 m range, which the cell does not contain.

### Images

Every extra or missing drawing in P1-10, P1-11, P1-12, and P1-14 was opened. The stored catalog image on an incomplete row was not replaced; the missing file was the one inspected.

| Drawing | What it shows | Recommendation |
| --- | --- | --- |
| `daa444bf…`, HDD rows 7–11 and 17 | Toshiba 1TB hard-disk label | Do not attach to product 18 or to the other five capacities. |
| `56ef1361…` | Purple drive label marked 6TB | Do not attach to the 3TB and 4TB WD rows. |
| `75b64d44…` | Purple drive label marked 6TB | Do not attach to the 6TB, 8TB, and 10TB WD rows as if each capacity had its own photo. |
| `26b0863c…`, 293×68 | ColorVu logo | Do not attach. This is the extra file on most of the 39 incomplete products, including product 25. |
| `04f0dea1…` | A “NEW” badge with a stock-site watermark | Do not attach to the EZVIZ rows that use it as the extra file. |
| Product 289’s three files | An indoor monitor, a door station, and a keypad station. Each also covers neighboring intercom rows. None prints `DS-KIS611-S`. | Do not attach the set. |
| Product 489’s 21 files | The anchors start at row 36 and run through later rows. One file is a Highway cable reel. Another is a junction box that also sits on row 35. | Do not attach the set. |
| Products 37, 184, 200, and 383 | Camera drawings that also sit on a neighboring model row. | Do not attach them to only one of those rows. |
| 522 `BNC` | Short cable tails. The picture does not say BNC. | Do not attach. |
| 524 connector jars | Jars of plugs, 98×75. Plausible, but small. | Leave unattached. A later quality decision can accept this one file. |
| 525 connector jars | Jars of plugs. The printed marking was not clear enough to confirm CAT6 or metal. | Do not attach. |
| 481 `M002` | Two junction-box bases. The small sticker was not readable as `M002`. | Do not attach. |
| 548 `4G R611C` | A MeFi 5G/4G router. The picture does not say `R611C`. | Do not attach. |
| `386a0f08…` | A lock branded Cougar | Do not attach to `Andel Q788`. It still does not print `Q799`. |
| `aa2a77f6…` | One magnetic lock, with no force rating | Do not attach to the 180 kg, 280 kg, and 350 kg rows. |
| `4273e7c0…` | One camera pedestal | Do not use it as both bracket lengths. |
| Switch drawings | A 16-port switch, a 24-port switch, and a separate 8-port unit | Do not use one front view for both the standard and Gigabit rows, and do not put the 8-port photo on the 4-port or 16-port rows. |

## Documentation note

The 16 October checkpoint in `docs/PROJECT_HANDOFF.md` records product 528 as a draft in unpublished category 38. The 17 October section now states the later published state, which matches `docs/unresolved-drafts.md` and the audit. The outdated draft sentence in that section was corrected.

## Current status — 18 October 2026

The checklist still has 22 items: 5 completed, 16 safe to leave unchanged, none waiting on a client, and 1 waiting on manufacturer documentation. The final verification is in `docs/phase-1-final-verification.md`. Phase 1 is ready to close. Product 18 stays unverified and unchanged.

Completed: P1-02, the description correction for products 433 and 434. P1-05, retention of the ES3216 specifications on products 447 and 448. P1-07, the SWITTEX name and neutral description on product 549. P1-08, 35 pence per month on product 449. P1-17, Uzbek and English descriptions for products 186, 398, 399, and 454, and short descriptions in all three languages for services 638, 639, 640, and 641.

Unresolved client decisions: none.

Awaiting authoritative evidence: P1-01, the product type of 18 `DS-10HKVS-VX1 1TB`.

Safe to leave unchanged: P1-03, P1-04, P1-06, and P1-09 through P1-16, plus P1-18 through P1-22. That includes the retained series descriptions, the `850 nm` unit, every reviewed image decision, the approved exceptions for products 13–17, 268, 494, 528, and 533, the 614 title fallbacks, the 49 digit-counter translations, all 639 prices, and the 117 category assignments.

Findings F085 and F086 in `docs/catalog-accuracy-audit.md`, and the product 433 and 434 entries in `docs/catalog-accuracy-review.md`, now keep the original 30–40 and 0.2–0.5 sentences as the 17 October finding and record the corrected public text. The 17 October handoff no longer says that product 528 and category 38 are still unpublished. `docs/unresolved-drafts.md` already matched that published state and was not changed.

## Phase 1 closure

Closed on 18 October 2026 as a catalog-correction phase. The detail is in `docs/phase-1-final-verification.md`.

An in-memory preview of the original Hikvision and EZVIZ workbooks was compared with the live source records. It was not applied. Product 549 matches `другие устройства` row 96. Its public name is `SWITTEX 1,8m`, its Russian description is locked, and a normal apply would keep that description. The stored source description would still be the LOGA paragraph. At the time of that check, choosing Accept Excel on that import row would have put the LOGA cell back into the Russian description and could have moved the category. That row-level override, the empty-brand clear, the case-sensitive `Ezviz` / `EZVIZ` lookup, and the missing warning for manual translations are now safeguards. They are described in `docs/phase-1-final-verification.md`. The live catalog was not edited for them.

Products 449, 433, 434, and 638–641 have locked Russian descriptions, so a normal apply would not replace those descriptions. Import never writes Uzbek or English. Products 186, 398, 399, and 454 still have unlocked Russian descriptions because that text was not edited; it currently matches the workbook, but a later cell change would be accepted by default.

Product 18 remains unverified. Hikvision’s 22 November 2024 HDD compatibility list and the datasheets checked for the neighbouring VX1 models do not contain `DS-10HKVS-VX1`. The description and missing image stay as they are.

## What this plan did not do

Phase 1A applied no correction. The later catalog edits are the completed description change for products 433 and 434 and the client-approved corrections recorded above. The closure check did not add another edit. Product 18 was not edited. Products 447 and 448 were not rewritten. Prices, images, categories, slugs, and source records were not edited. The workbooks were not saved. No import was applied, and no migration, restart, commit, push, or deployment was run.
