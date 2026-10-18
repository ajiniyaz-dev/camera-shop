# Phase 1 — final verification

18 October 2026. This check followed the client-approved catalog corrections. It did not change application code, catalog rows, prices, images, categories, slugs, source records, or the Excel workbooks. No import was applied to the live catalog.

## Checklist

The plan still has 22 items. The counts are unchanged by this check.

| Status | Items | IDs |
| --- | ---: | --- |
| Completed | 5 | P1-02, P1-05, P1-07, P1-08, P1-17 |
| Safe to leave unchanged | 16 | P1-03, P1-04, P1-06, P1-09 through P1-16, P1-18 through P1-22 |
| Needs client decision | 0 | |
| Needs further verification | 1 | P1-01, product 18 |
| Total | 22 | |

5 + 16 + 0 + 1 = 22. Product 18 is not marked verified.

## Client-approved changes already completed

| Products | What was applied | Fields |
| --- | --- | --- |
| 433, 434 | Removed the 30–40 people/min and 0.2–0.5 s claims in Russian, Uzbek, and English. The 5–60 s door-open duration was not added. | `description` ru, uz, en. Locked, origin `manual`. |
| 447, 448 | Client accepted the existing ES3216 specifications. No text was rewritten. | None. |
| 549 | Public model and ru/uz/en titles are `SWITTEX 1,8m`. Public description is `SWITTEX 1,8m.` The LOGA specification is not public. Slug remains `product-swittex-1-8m`. | `model_display`, and the admin save also set `model_raw`, `model_normalized`, and `model_locked`. Titles and descriptions in ru, uz, en. |
| 449 | 35 pence per month replaced the people-per-minute sentence in ru, uz, and en. The other measurements stayed. | `description` ru, uz, en. Locked, origin `manual`. |
| 186, 398, 399, 454 | Uzbek and English translations of the existing Russian descriptions. Russian text was not edited. | `description` uz, en. Those rows are locked and `manual`. Russian stays origin `source` and unlocked. |
| 638, 639, 640, 641 | Short service descriptions in ru, uz, and en. Monthly on 638 and 639, yearly on 640 and 641. | `description` ru, uz, en. Locked, origin `manual`. |

`api/tests/test_catalog_admin.py` was run earlier on a disposable database: 8 passed, with one Starlette deprecation warning for httpx. The published count remained 639. This verification did not repeat that test.

## How this check was made

The running importer was read, including `api/app/importing/match.py`, `apply.py`, and `stage.py`. The same functions are in the running API image. Existing tests were read. They cover a locked price and a manual Russian title. They do not assert that `description_locked` survives apply, and `origin = manual` is not what the importer consults for a description.

The original `data/source/Hikvision pr.xlsx` and `data/source/Ezviz pr.xlsx` were parsed in memory with `read_workbook`. `match_rows` was then run against the live source records with `replace_prices` false. Nothing was staged, applied, or saved. The workbooks were not written.

`description_locked` is read only from the Russian translation. A locked Russian description becomes `keep_current`. An unlocked difference becomes `accept_excel`. `origin` does not enter that decision. Apply writes a description only when `_accepts_field` accepts it, and that write updates only the Russian row. Uzbek and English are never filled from the workbook.

`source_description_raw` is not the text the preview compares. The preview compares the newly parsed workbook cell with the public Russian description. On a matched apply, including one that keeps the public description, `_refresh_source` still copies the workbook cell into `source_description_raw`, `source_description_sha256`, and `match_key`.

The row action Accept Excel is a separate, explicit step. It changes every `keep_current` field on that row to `accept_excel` before apply. A normal apply does not take that step.

## Product 549

The live row and the workbook row are the same product.

| Field | Live value | Workbook row 96, `другие устройства` |
| --- | --- | --- |
| Model | `model_display`, `model_raw`, `model_normalized`, and `source_model_raw` are `SWITTEX 1,8m`. `model_locked` is true. | Cell C96 parses as `SWITTEX 1,8m`. |
| Slug | `product-swittex-1-8m`. Import apply does not change slugs. | Not in the match key. |
| Public description | `SWITTEX 1,8m.` in ru, uz, and en. All three are locked and `manual`. | The description cell is the LOGA paragraph. |
| Source description | `source_description_raw` is still that LOGA paragraph. Its stored hash is the hash inside `match_key`. | Same paragraph. The preview matched this key to product 549 only. |
| Category | `Сетевые фильтры`, category 46, `category_locked` true. | Proposed category `другие устройства`. |
| Price and brand | $2.80, no brand. Neither was a preview change. | Unchanged in the comparison. |

No other published product uses the normalized model `swittex 1,8m`. The match key is source, worksheet, normalized model, option, and the description hash. That key still identifies row 96, so the import does not attach this product to a different Excel row.

A normal preview is an update with resolution `keep_current`. The two differences are the description and the category, and both resolutions are `keep_current`. Apply would not write the public description, the model, the slug, or the category. It would refresh the source record from the workbook, which leaves the LOGA paragraph in `source_description_raw`. That field is historical import evidence. It does not become the public description unless the description resolution is `accept_excel`.

The gap is the row-level Accept Excel action. One choice on this row would turn both `keep_current` decisions into `accept_excel`. The Russian description would become the LOGA paragraph again. Uzbek and English would stay `SWITTEX 1,8m.` The category could move from `Сетевые фильтры` to `другие устройства`. That is explicit, and it is broader than accepting one field.

Minimal safeguard, not implemented: do not let the row-level Accept Excel action override a locked description. Require a separate confirmation for that field. Until that exists, do not choose Accept Excel for product 549.

## Approved descriptions and translations

| Products | Russian lock | Preview against the original workbooks | Normal apply |
| --- | --- | --- | --- |
| 449 | Locked. Public text differs from the workbook sentence. | Exact match to СКУД row 48. Only change is the description, resolution `keep_current`. | Public description stays 35 pence per month. The source copy stays the workbook sentence. Accept Excel on the row would replace the Russian description with the whole workbook cell. |
| 433, 434 | Locked. Public text no longer has the removed claims. | Exact match to empty cells D32 and D33, because `match_key` still uses the empty-description hash. Description resolution `keep_current`. | Public descriptions stay. Accept Excel on the row would clear the Russian description because the cell is empty. Uzbek and English would remain. A normal apply would still refresh `source_description_raw`, so the stored pre-correction paragraph would be replaced by the empty cell. |
| 638–641 | Locked. Public text is the new service sentence. Workbook cells are empty. | Exact match by model plus billing option. The duplicate service names stay separate. Description resolution `keep_current`. | Public descriptions stay. Accept Excel on the row would clear the Russian description. |
| 186, 398, 399, 454 | Russian is not locked. Uzbek and English are locked, but the importer does not read those locks. | Exact match. The workbook description equals the public Russian description, so description is not listed as a change. | The Russian wording would stay only because it already equals the cell. A later change in that cell would be accepted by default and would not update Uzbek or English. |

The current locks are sufficient for a normal apply of these workbooks for 449, 433, 434, and 638–641. They are not sufficient for 186, 398, 399, and 454 if the workbook cell later changes. `origin = manual` does not close that gap.

Two other preview results are not description changes, and they were not applied:

- Products 186, 398, 399, 454, 433, and 434 show the workbook brand as empty while the catalog brand is Hikvision. Where that field is `accept_excel`, a normal apply would clear `brand_id`. For 186, 398, 399, and 454 the row resolution is `accept_excel`, so that brand clear would happen together with rewriting the Russian description to the same current text.
- Products 638–641 show category `Ezviz` against the stored Russian name `EZVIZ`, with category resolution `accept_excel`. Category lookup is case-sensitive, so a normal apply could create a second category and move those four services. Their descriptions would still be kept.

Those brand and category results are existing importer behavior. They are follow-up work before anyone applies these workbooks. They are not a reason to edit the approved descriptions now.

## Product 18

The product type remains unverified. The description and the missing image should stay unchanged. The Toshiba drawing stays unattached.

Checked on 18 October 2026:

- Hikvision’s HDD compatibility list dated 22 November 2024, `HDD-Compatible-List-for-Hikvision-DVR-NVR-20241122.pdf` on hikvision.com, lists `DS20HKVS-VX1`, `DS40HKVS-VX1`, `DS60HKVS-VX1`, and later `DS80HKVS-VX1`, `DS120HKAI-VX1`, and `DS160HKAI-VX1`. The extracted text does not contain `DS-10HKVS-VX1` or `DS10HKVS-VX1`.
- Datasheets found for `DS20HKVS-VX1`, `DS40HKVS-VX1`, and `DS60HKVS-VX1` do not list `DS-10HKVS-VX1`.
- The Hikvision USA 2025 product quick guide extract does not contain this model.
- A reseller page uses the exact string and calls it a 1 TB surveillance drive. The same page also names `DS10HKVS-VX2`. It is not a manufacturer document and is not used.
- An EU declaration names `DS10HKVS-VX1`, without the hyphen and without `1TB`, as a digital video recorder. That is a different string and is not used.

The catalog description still calls it a Hikvision surveillance hard drive of 1 TB. That sentence stays a claim, not a verified type. The `1TB` token in the model cell is not evidence of the device type.

The same in-memory preview matches product 18 to HDD row 17. The description cell is empty, the Russian description is locked, and the description resolution is `keep_current`. A normal apply would not clear that description. This check did not apply it.

## Remaining follow-up

1. A live import of the original workbooks was not run. The next apply should still be reviewed in preview. Accepting one field can still replace that field, including a locked description, and a matched apply still refreshes `source_description_raw`.
2. Products 186, 398, 399, and 454 still have unlocked Russian descriptions. A later cell change is flagged when Uzbek or English text is manual, and those translations are not overwritten. The Russian text would still be accepted by default. Locking it would be a catalog edit and was not done.
3. Existing brand assignments and category rows were not bulk-edited. Future imports keep an assigned brand when the cell is empty, and they reuse `EZVIZ` when the workbook says `Ezviz`.
4. Leave product 18 unchanged until a manufacturer document uses the exact model `DS-10HKVS-VX1`.

## Import safeguards

Implemented after the read-only check above, without applying an import or editing the live catalog.

| Safeguard | Behavior |
| --- | --- |
| Locked fields | Row-level Accept Excel no longer changes every `keep_current` field. A locked description, category, price, brand, option, or display model stays until that field is accepted on its own. The preview confirmation names the fields that stay, and each field has a separate confirmation. |
| Empty brand | A blank source brand is a `keep_current` change with message `brand_absent`. Apply does not clear the assigned brand. A non-empty brand still follows the lock rules. An explicit field decision can still replace or remove a brand. |
| Category names | Lookup folds case and internal whitespace. `Ezviz` and `  ezviz  ` reuse a stored `EZVIZ` category on the same parent, source, and worksheet. The stored name and slug are not rewritten. A different title, parent, source, or worksheet stays a different category. |
| Manual translations | When the Russian description differs and a non-empty manual Uzbek or English description exists, the row message is `manual_translations_stale`. Those texts are not overwritten and are not translated automatically. An unchanged Russian description, or a product with no such translation, does not add the message. |

No schema migration was added. The field decision is an optional body on the existing row PATCH. The warning is a message on the staged row.

### Tests

Run on disposable Postgres `cs-pytest-pg`, not the Compose catalog. The container was removed after the run.

| Tests | Result |
| --- | --- |
| `api/tests/test_import_api.py` | 17 passed |
| `api/tests/test_import_stage.py` | 11 passed |
| `api/tests/test_catalog_admin.py` | 8 passed |
| `web` `npm run typecheck` | Passed |

36 tests passed. One Starlette deprecation warning came from httpx with the test client.

The new cases cover product 549’s locked description and slug on a synthetic row, another locked description through that same path, an explicit description override, an empty brand that stays, a populated brand that is assigned, an explicit brand removal, `Ezviz` against `EZVIZ`, extra whitespace, a different category and a different worksheet, a changed Russian description with manual translations, an unchanged Russian description, and a missing translation.

### Limitations that remain

- Product 18 is still unverified. Its description, price, category, image, and type were not changed.
- `source_description_raw` is still copied from the workbook on a matched apply, including when the public description is kept. For products 433 and 434 a future apply can replace the stored pre-correction paragraph with the empty cell without changing the public text.
- Products 186, 398, 399, and 454 are only flagged, not locked.
- Accepting one field still writes that field. That is the explicit approval the preview asks for.
- Live category and brand rows were not rewritten, so the stored `EZVIZ` name and existing Hikvision assignments stay until a future reviewed import.

## Recommendation

Phase 1 is operationally ready to close. The client-approved corrections are in place, the checklist totals 22, and the four import gaps found by the read-only preview are now safeguards in the importer. Product 18 stays unverified and unchanged. It is not a blocker and it is not a catalog edit. No live import was applied.
