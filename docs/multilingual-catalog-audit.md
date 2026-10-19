# Multilingual catalog audit

**Date:** 19 October 2026
**Checkpoint:** `3b6b1c15133c1fa14acbc68589089da3b1f52c8a` (`Polish multilingual catalog, cart, and SEO`)
**Scope:** Read-only audit of live local Docker Postgres + public API. No files, rows, imports, or services were modified during data collection. This document is the audit deliverable only.

**Sources of truth used:**
- Database tables `products`, `product_translations`, `categories`, `category_translations`, `brands`, `brand_translations`, `product_source_records`
- Public API via `http://127.0.0.1:8080/api/public/...`
- Application logic in `api/app/public/router.py` (`_text`, `_card`, `_detail`)

Workbook cells were **not** re-read for this audit. Source worksheet/row on findings come from stored `product_source_records` only.

---

## A. Executive summary

### Inventory (live local catalog)

| Entity | Count |
|--------|------:|
| Published products (`deleted_at` null) | 639 |
| Draft products | 0 |
| Archived products | 0 |
| Soft-deleted products | 0 |
| Categories (all published) | 48 |
| Published brands | 7 (of 8 total; brand `other` unpublished) |

### Product translation rows (`product_translations`)

Every published product has **ru**, **uz**, and **en** rows (0 missing rows).

| Locale | Rows | Blank / NULL `localized_name` | Blank / NULL `description` |
|--------|-----:|-------------------------------:|----------------------------:|
| ru | 639 | 0 | 0 |
| uz | 639 | 612 | 0 |
| en | 639 | 612 | 0 |

Of the 612 blank UZ/EN names:

| Class | Count | Public UX |
|-------|------:|-----------|
| Cyrillic Russian title → UZ/EN fallback with `translation_fallback: true` | **24** | Confirmed issue: Russian title + “In Russian” / “Rus tilida” note |
| Latin / model-code Russian title → silent reuse | **588** | Blank name rows, but API clears fallback when the resolved title has no Cyrillic (same as prior P1-18 posture) |

Products with **filled** UZ and EN names: **27** (26 identical model-code triples; **1** truly localized: product 528).

### Category translations

| Locale | Rows | Missing | Blank names |
|--------|-----:|--------:|------------:|
| ru / uz / en | 48 each | 0 | 0 |

No category has UZ/EN name equal to a Cyrillic Russian name. Parent/child links: 15 children, 0 orphan parents, 0 self-parents.

### Previously fixed records (verified)

| Record | Status |
|--------|--------|
| Category 38 `drugie-ustroystva` | RU `другие устройства`, UZ `Boshqa qurilmalar`, EN `Other devices`; API `translation_fallback: false` for all three |
| Product 528 `product-gibkiy-perekhod` | RU/UZ/EN localized names present; API name fallback false; **model_display remains** `гибкий переход` |

### Totals by confidence

| Bucket | Count |
|--------|------:|
| Confirmed product title fallback issues (Cyrillic + blank UZ/EN) | 24 |
| Suspicious descriptive `model_display` values (includes 528; overlaps title set) | 25 Cyrillic models |
| Blank UZ/EN name rows that silently reuse Latin model titles | 588 (informational / established policy) |
| Category translation gaps | 0 |
| Uncertain “identical across locales” among filled names | 26 model codes (expected) |

---

## B. Detailed findings

### B1. Confirmed: Cyrillic product titles missing UZ/EN `localized_name`

**Issue type:** Blank UZ/EN localized name → public API falls back to Russian title with `translation_fallback: true`.
**Evidence:** DB null names + `GET /api/public/products/{slug}?locale=uz|en` returned Russian `name` and `translation_fallback: true` for every row below.
**Recommended action:** Add natural UZ/EN `localized_name` values (and keep descriptions as-is). Prefer translating the descriptive phrase; keep genuine model tokens (e.g. `T311`, `EM-Marine`, `CS-SD7`) unchanged.
**Confidence:** **high**

| ID | Model / current RU title | Category slug | Source worksheet / row | UZ/EN API name | Fallback |
|----|--------------------------|---------------|------------------------|----------------|----------|
| 25 | `IPC-B429H (С)` | colorvu | Hilook / 9 | same | true |
| 444 | `Турникет T311` | skud | СКУД / 43 | same | true |
| 445 | `Турникет T315` | skud | СКУД / 44 | same | true |
| 462 | `Замок 180кг` | skud | другие устройства / 9 | same | true |
| 463 | `Замок 280кг` | skud | другие устройства / 10 | same | true |
| 464 | `Замок 350кг` | skud | другие устройства / 11 | same | true |
| 468 | `карта EM-Marine` | skud | другие устройства / 15 | same | true |
| 469 | `Брелок` | skud | другие устройства / 16 | same | true |
| 477 | `Кронштейн 20SM M-611` | montazhnye-prinadlezhnosti | другие устройства / 24 | same | true |
| 478 | `Кронштейн 30SMX60SM M-901` | montazhnye-prinadlezhnosti | другие устройства / 25 | same | true |
| 479 | `Кронштейн 30SM M-612` | montazhnye-prinadlezhnosti | другие устройства / 26 | same | true |
| 480 | `Кронштейн 60SMX120SM M-901` | montazhnye-prinadlezhnosti | другие устройства / 27 | same | true |
| 511 | `Блок розеток` | komplektuyushchie-dlya-shkafov | другие устройства / 58 | same | true |
| 512 | `фальшпанель` | komplektuyushchie-dlya-shkafov | другие устройства / 59 | same | true |
| 513 | `Патч-панель` | komplektuyushchie-dlya-shkafov | другие устройства / 60 | same | true |
| 514 | `органайзер` | komplektuyushchie-dlya-shkafov | другие устройства / 61 | same | true |
| 515 | `Панель-заглушка` | komplektuyushchie-dlya-shkafov | другие устройства / 62 | same | true |
| 621 | `CS-SD7 Умный экран` | ezviz | Ezviz / 66 | same | true |
| 636 | `CS-T30-10B-EU Умная розетка` | ezviz | Ezviz / 81 | same | true |
| 637 | `CS-T31-16E-EU Умная розетка` | ezviz | Ezviz / 82 | same | true |
| 638 | `7-дневная видеоистория событий` | ezviz | Ezviz / 83 | same | true |
| 639 | `30-дневная видеоистория событий` | ezviz | Ezviz / 84 | same | true |
| 640 | `7-дневная видеоистория событий` | ezviz | Ezviz / 85 | same | true |
| 641 | `30-дневная видеоистория событий` | ezviz | Ezviz / 86 | same | true |

Notes:
- IDs **638–641** are `product_kind = service`. Pairs 638/640 and 639/641 share the same title; billing period is distinguished by `option_label` (monthly vs yearly), not by the localized name.
- ID **25** is flagged only because of Cyrillic `С` in parentheses; the rest of the string is a HiLook model code. Treat as **high** for fallback flag, **medium** for whether a translation is needed beyond normalizing the parenthetical character.

### B2. Suspicious / descriptive `model_display` values

**Issue type:** Model field holds a descriptive phrase (often identical to Russian title), not only an equipment code.
**Evidence:** `model_display ~ '[А-Яа-яЁё]'` on 25 published products; all match Russian `localized_name`.
**Recommended action:** Human review per product. Options: keep as catalog identity (workbook model cell was descriptive), or introduce a clearer model token while keeping the localized title—**do not invent part numbers**.
**Confidence:** **high** for “descriptive model string”; **medium** for “must change model_display”.

Includes all Cyrillic rows in B1 plus product **528** (`гибкий переход`), whose **titles** are already localized but whose **model** field remains Russian.

### B3. Blank UZ/EN names on Latin model-code titles (informational)

**Count:** 588 published products.
**Issue type:** Translation rows exist; `localized_name` is NULL for uz/en.
**Public API:** Resolves to the Russian title (typically the same Latin model string) and sets `translation_fallback: false` because the resolved text has no Cyrillic (`_card` in `public/router.py`).
**Example:** `hilook-ipc-b129ha-lu` → UZ/EN name `IPC-B129HA-LU`, fallback `false`.
**Recommended action:** **Retain** under current product policy (model codes need not be duplicated into uz/en). Optional cleanup: copy `model_display` into uz/en names for consistency of stored rows only.
**Confidence:** **high** that behavior matches design; **low** as a customer-facing defect.

### B4. Filled names that are identical across RU/UZ/EN

**Count:** 26 of 27 filled triples (all except 528).
**Examples:** `DS-2CD1047G2-L`, `GDR-126035B`, `12V 15A`, `SWITTEX 1,8m`.
**Recommended action:** **Retain** — legitimate unchanged model / commercial identifiers.
**Confidence:** **high**

### B5. Category translations and hierarchy

- No missing category translation rows; no blank names.
- Category 38 verified localized (see above).
- 14 categories share the same name in all locales (HDD, ColorVu, DVR, EZVIZ, series names, etc.) — expected brand/series labels.
- 34 categories differ by locale (translated section names).
- No broken parent references among 15 child categories.

**Recommended action:** None for categories based on this audit.
**Confidence:** **high**

### B6. Brands

Published brands: full ru/uz/en name rows, 0 blanks. Unpublished brand `other` excluded from public navigable set by existing rules. Not a finding.

### B7. Descriptions

All 639 × 3 description fields are non-blank in the database. No blank-description findings. (Whether every description is a high-quality translation was **not** scored sentence-by-sentence.)

---

## C. Suggested fixes (wording only — not applied)

Suggestions below translate the **descriptive** part of the title. Model tokens stay. Marked **needs human confirmation** where marketing nuance or hardware type is ambiguous. **Do not invent technical specifications.**

| ID | Suggested EN name | Suggested UZ name | Notes |
|----|-------------------|-------------------|-------|
| 25 | `IPC-B429H (C)` or keep as-is | same | Likely Latin C mistyped as Cyrillic С; confirm |
| 444 | Turnstile T311 | Turniket T311 | Confirm “turnstile” vs product type |
| 445 | Turnstile T315 | Turniket T315 | same |
| 462 | Lock 180 kg | Qulf 180 kg | Magnetic/electric lock type not asserted |
| 463 | Lock 280 kg | Qulf 280 kg | |
| 464 | Lock 350 kg | Qulf 350 kg | |
| 468 | EM-Marine card | EM-Marine karta | |
| 469 | Key fob | Breloq | |
| 477 | Bracket 20SM M-611 | Kronshteyn 20SM M-611 | Keep size/model tokens |
| 478 | Bracket 30SM×60SM M-901 | Kronshteyn 30SM×60SM M-901 | |
| 479 | Bracket 30SM M-612 | Kronshteyn 30SM M-612 | |
| 480 | Bracket 60SM×120SM M-901 | Kronshteyn 60SM×120SM M-901 | |
| 511 | Power strip / outlet block | Rozetkalar bloki | Confirm product type |
| 512 | Blanking panel | Yosirma panel / falshpanel | Confirm preferred UZ term |
| 513 | Patch panel | Patch-panel | |
| 514 | Cable organizer | Organayzer | |
| 515 | Blanking panel | Panel-zaglushka | Distinguish from 512 if needed |
| 621 | CS-SD7 Smart screen | CS-SD7 aqlli ekran | |
| 636 | CS-T30-10B-EU Smart plug | CS-T30-10B-EU aqlli rozetka | |
| 637 | CS-T31-16E-EU Smart plug | CS-T31-16E-EU aqlli rozetka | |
| 638 / 640 | 7-day video event history | 7 kunlik video voqealar tarixi | Keep billing on `option_label` |
| 639 / 641 | 30-day video event history | 30 kunlik video voqealar tarixi | same |
| 528 model | *(titles already OK)* | | Optional: leave model as Russian phrase or set model to a neutral token; **human decision** |

---

## D. Coverage and limitations

**Checked**
- All 639 published products’ translation row presence and blank name/description counts.
- All 48 categories’ translation completeness and parent integrity.
- API fallback flags for all 24 Cyrillic blank-name products, product 528, category 38, and a Latin model-code control (`IPC-B129HA-LU`).
- Public category tree + category detail breadcrumb for `drugie-ustroystva` (UZ).

**Not checked / not claimed**
- Full manual browser pass of every product page.
- Sentence-level quality of the 639×3 descriptions.
- Re-opening Excel workbooks for cell-level comparison (only stored `source_worksheet` / `source_row`).
- Draft/archived products (none present).
- Spec-name/spec-value translations (out of title/model scope for this report’s primary tables; not exhaustively counted).

**Unpublished / unavailable**
- Brand `other` unpublished — expected.
- No draft products to examine.

---

## E. Verification (read-only)

| Check | Result |
|-------|--------|
| `git status` / HEAD | Clean working tree; `main` at `3b6b1c1`, synced with `origin/main` |
| Docker services | postgres, api, web, nginx healthy |
| SQL inventory | 639 published, 0 draft/archived/deleted; 48 published categories |
| SQL translation coverage | Product missing rows 0; blank UZ/EN names 612; blank descriptions 0; category gaps 0 |
| SQL category 38 / product 528 | Localized names present as previously fixed |
| `GET /api/public/categories?locale=*` | Category 38 names + `translation_fallback: false` |
| `GET /api/public/products/product-gibkiy-perekhod?locale=*` | Localized names; name fallback false; model still `гибкий переход` |
| `GET /api/public/products/{slug}?locale=uz\|en` for 24 Cyrillic-title SKUs | All `translation_fallback: true` with Russian names |
| `GET .../hilook-ipc-b129ha-lu?locale=uz\|en` | Latin title, `translation_fallback: false` |
| Data / code mutations | **None** during audit queries; this markdown file is the only intentional write after verification |

---

## Resolution path (awaiting approval)

1. Decide whether the 588 Latin blank UZ/EN names stay as policy or get mirrored model strings.
2. Approve translations (or edits) for the **24** Cyrillic-title products in B1.
3. Separately decide whether descriptive `model_display` values should remain workbook-faithful or be normalized without inventing codes.
4. Apply approved changes only after explicit go-ahead — not part of this audit.
