# Import strategy

Deterministic importer inside the FastAPI process. It does not call an AI service. It does not modify `data/source/*.xlsx`. It writes a copy of each upload and new image files only.

The live catalog changes only when an administrator applies a job. Upload and preview write staging tables and media objects, not `products` public fields.

Google Sheets is not a source. The client keeps local Excel files.

## Sources

| Source code | Expected filename (evidence only) | Structural signature |
| --- | --- | --- |
| `ezviz` | `Ezviz pr.xlsx` | A header row containing `Модель` and `Цена для дилера` |
| `hikvision` | `Hikvision pr.xlsx` | One or more header rows containing `Модель` and `Цена`, and no `Цена для дилера` price header |

Filename agreement strengthens identification. It is not sufficient and it is not required.

- If the signature matches one source, identify it automatically.
- If the filename and the signature disagree, stop that file and ask the administrator to confirm the source. Do not import it into the signature’s source or the filename’s source until they confirm. After confirmation, the required columns for the confirmed source must still be present.
- If the file matches neither signature, or matches both, validation fails for that file. The administrator may confirm a source only when the required columns for that source exist. Otherwise the file is rejected.
- A file is never applied to the other source’s mappings.

Future layout changes are handled by failing validation when a required header disappears, not by guessing a shifted meaning. A new optional column is reported and left unmapped until this mapping document is updated.

## Jobs

An `import_jobs` row is one review and one **Apply approved changes** action.

| Scenario | Files in the job | What may change |
| --- | --- | --- |
| A. Only Hikvision changed | one `hikvision` file | Hikvision-source products only |
| B. Only EZVIZ changed | one `ezviz` file | EZVIZ-source products only |
| C. Both changed | both files | Both sources, still stored as two `import_files` |
| D. One file not uploaded | the file that was uploaded | The missing source is untouched. Absence of a file is not deletion |
| E. One file invalid | the valid file may be applied; the invalid file is `included_in_apply = false` | The invalid file changes nothing. If the administrator does not apply the valid file, the live catalog stays as it was |

The preview states which source files are included and which source was not part of the job.

A job cannot contain two files with the same source code. Uploading a second Hikvision file means a new job or a replacement of the staged Hikvision file before preview is confirmed, not two Hikvision sources in one apply.

## 1. Store and validate

- Administrators only. `.xlsx` only. 40 MB per file. ZIP signature and `xl/workbook.xml` required.
- Macros are not executed. Cached cell values are read. A formula with no cached value is an invalid cell, not a calculated guess. The current workbooks contain no formulas.
- Copy each file to `media/imports/{job_id}/{source_code}.xlsx`.
- Record original filename, SHA-256, identifier, and validation errors on `import_files`.
- Unknown sheets are accepted only when they contain the recognized header pair for that source. A sheet missing `Модель` or the source’s price header fails that sheet and is listed on the file. It does not delete existing products.

## 2. Parse and classify

Walk rows after the header. Locate columns by header text, not by fixed letters.

| Class | Rule | Becomes a product? |
| --- | --- | --- |
| `blank` | Mapped cells empty | No |
| `heading` | No model, description, or price, and column A is non-numeric text | No. Category proposal |
| `stray` | No model, and the only value is a number (`1`, `11`, `17` in the current files) | No |
| `service` | EZVIZ cloud-history names, or option `Ежемесячно:` / `Ежегодно:` | Yes, `product_kind = service` |
| `product` | Model present, not a service | Yes |
| `invalid` | Model present but the price text is not empty, numeric, or `по запросу` | Held out of apply until fixed |

Hilook’s 28 section labels are headings, not products. A heading applies to following product rows until the next heading. A heading with no products of its own is proposed as a parent category. The preview shows that tree.

Normalize without destroying `raw_cells`:

- Display model: trim and collapse whitespace.
- Normalized model: case-fold the display model. Unicode dashes fold to `-` only inside the key.
- Description: trim the ends, preserve internal text, SHA-256 the result.
- Option: trim; empty is null.
- Numeric cell: `numeric(12,2)`, including `92.5` and `0.1`. Not a binary float. Not an integer rounding.
- `по запросу` after trim and case-fold: source kind `explicit_on_request`.
- Empty price: source kind `blank`. Public proposal `on_request`, amount null. Not zero.
- Any other price text: invalid. No invented number and no substituted discount.
- Currency on a numeric proposal is `USD`. The cell itself has no currency token; USD is the confirmed business rule, not a conversion.
- Hilook column F, which has no header, is `internal_note` only when it sits immediately to the right of `Цена`. It is not parsed as a price. Verified cells `F103`, `F106`, `F107`, and `F115` therefore do not change the amounts in `E103`, `E106`, `E107`, and `E115`.

Brand proposal:

- EZVIZ workbook: brand `EZVIZ`.
- A row whose model or description identifies HiLook, Hikvision, WD, Seagate, Andel, or Cougar: that brand.
- Otherwise brand is null and the row is `review`. The company name is not used as a fallback manufacturer.

Russian description proposal writes `product_translations` for `ru` only.

Stock is not present in the files and is not part of the proposal. New products start `in_stock`.

## 3. Identity and matching

Do not match on model name alone. Do not match on row number alone. Row number is stored after a match.

Match key:

```text
source_code + worksheet + model_normalized + normalized option + description sha256
```

Compare only with `product_source_records` of the same `source_code`.

| Incoming row | Action |
| --- | --- |
| Exact key exists for one product of this source | `update` if any mapped field differs, otherwise `unchanged` |
| Exact key exists for more than one product | `conflict`. No write |
| No exact key, but exactly one unmatched existing record and exactly one unmatched incoming row share source, worksheet, model, and option | `possible_match`. Excluded until the administrator accepts it |
| Same normalized model, different key, not a unique pair | Separate products, plus a duplicate warning. No merge |
| No candidate | `insert` |

Accepting a `possible_match` updates that product and replaces its match key with the new description hash. It does not insert a second product.

Re-uploading a byte-for-byte unchanged file produces exact keys and `unchanged` rows. Apply does not insert duplicates and does not rewrite public fields that are already equal.

A product with no source record (created in admin) is invisible to matching.

## 4. Images

Read drawing anchors. Do not zip images to rows by order.

1. Extract PNG, JPEG, and WebP only. Reject other types onto the report and keep the product.
2. Write bytes once at `media/objects/{sha256[0:2]}/{sha256}.{ext}`.
3. Top-left anchor on a model row in the `Фото` column: `linked_high`.
4. Top-left anchor on a model row in another column: `linked_review`. Not public until confirmed.
5. Top-left anchor not on a model row: `unassigned`. Not attached to the nearest product.
6. A merged `Фото` range that covers extra model rows with no anchor of their own: `shared_candidate` for those extra rows. Do not copy the file onto them.
7. A tall anchor that overlaps the next row does not assign the image to that next row.

Several high-confidence images on one row all belong to that product. The first becomes primary only when the product does not already have an administrator-chosen primary.

Unassigned and shared-candidate assets stay on `import_assets` for the job report.

Current-file consequences the report must be able to show: 762 images; 571 model rows with an image starting on that row; 68 without; 10 images on non-product rows; a 27-image stack on one `другие устройства` row. Those figures are measured in `docs/excel-data-analysis.md`.

## 5. Manual edits and resolutions

Protected fields: public price, Russian description, option, brand, category, and display model.

| Situation | Default resolution |
| --- | --- |
| Field unlocked, or new product | Accept the Excel value |
| Field locked | `keep_current` |
| Job flag `replace_prices` | Price conflicts default to `accept_excel` |

The preview lists every locked value that will be kept and, if `replace_prices` is on, every manual price that will be replaced. The administrator can flip a row to the other resolution or exclude the row.

SEO fields, slugs, stock, `hidden` prices, archive status, and `uz` / `en` translations are never written by the importer.

## 6. Preview

Staging sets the job to `preview`. Live `products` rows are unchanged.

Show, separately per source and as a combined total:

- New products, updates, and unchanged rows.
- Price changes, including blank-to-request initialization on first import.
- Description changes.
- Category and brand changes, and rows with no verified brand.
- New or changed images.
- Possible duplicate model names.
- Invalid records.
- Ambiguous image associations and unassigned images.
- Rows that need a match decision.
- Products of this source that are absent from the uploaded file.
- Conflicts with manual edits and the resolution that apply would use.
- Headings, stray rows, and ignored blank rows.
- Internal discount notes detected, with the public amount unchanged.

The administrator does not approve every field one by one. Defaults cover the confident rows. They exclude `possible_match`, unresolved conflicts, and invalid rows until those are resolved or left excluded.

## 7. Apply once

**Apply approved changes** is one action for every included file in the job.

1. Reject the call unless status is `preview`.
2. Begin one database transaction.
3. Set status to `applying` and set `approved_by`.
4. For each included valid file, and for no other source:
   - Insert accepted brands and categories.
   - Insert new products, Russian translations, public USD prices, and source records. Locks are false. Stock is `in_stock`. Slug is allocated once. `catalog_status` follows the job’s publish choice for new rows (default published for a first load, visible in the preview).
   - Update matched products according to resolutions. Always refresh that source snapshot, `last_job_id`, and `last_seen_at`.
   - Link approved images. Skip checksums the product already has. Do not delete images the file no longer contains and do not delete administrator-uploaded images.
   - Mark this source’s mappings that were not in the file `absent_from_latest`. Do not archive them and do not change the other source’s flag.
5. Write the summary and an audit-log row.
6. Commit and set status `applied`.

Any error rolls the transaction back, sets `failed`, and stores `error_message`. Live catalog tables match the pre-apply state.

The transaction is the whole apply, not one product at a time.

A repeated request after `applied` returns the stored result and does not write again.

## Filesystem and database

Database transactions do not cover the disk.

- Objects are written by checksum before apply. Writing the same checksum twice is the same file.
- The transaction only inserts or points at keys.
- If the transaction rolls back, new keys may be unreferenced. They are harmless and may be deleted later by a cleanup that removes keys no table references. Cleanup must not delete a key that `product_images` or another asset still uses.
- If the process dies after commit and before the HTTP response, the job is already `applied`. The client retry sees `applied` and stops.
- If the process dies during `applying` before commit, the database rolls back when the connection drops, and the job remains `preview` or is marked `failed` by a startup check of jobs stuck in `applying`. Stuck `applying` with no committed catalog changes is returned to `failed` so it cannot be double-applied. The administrator starts a new job.
- Live objects already referenced by published products are never deleted as part of a failed job.

## First import

- Both workbooks are imported, together or as two jobs.
- Legitimate products and category proposals are created.
- EZVIZ public prices come from `Цена для дилера` in USD.
- Hikvision public prices come from `Цена` in USD, never from a discount note.
- Explicit `По запросу` stays the request-price state.
- Blank prices become public `on_request` and source kind `blank`.
- Verified brands are stored. Unclear brands are null and flagged.
- High-confidence anchors are linked. Other images are kept for review.
- Uncertain identities are excluded from apply until confirmed.

## Later imports

- Only sources included in the job are compared or updated.
- The source that was not uploaded keeps its products, prices, images, and absent flags.
- Changes are measured against that source’s current mapping and the live catalog.
- Locked fields stay unless the resolution accepts Excel.
- An unchanged workbook does not create duplicates.
- Repeated model names are not merged.
- Missing source rows are not deleted.
- The preview is before apply, and the job summary is the report after apply.

## Report contents

Per source and combined:

- Inserted, updated, unchanged, excluded, conflicts, needs review, failed.
- Prices kept because they were locked, and prices replaced because the administrator accepted Excel or enabled `replace_prices`.
- Counts of numeric, explicit request-price, and blank source cells.
- Image counts by high, review, shared candidate, and unassigned.
- Blank rows, headings, stray rows, invalid rows.
- Absent products for the uploaded source only.
- The exception message when the job fails.

Do not mark the job successful when apply rolled back. A job can be `applied` while some rows were excluded; the summary must count those exclusions and must not call them successes.

## Safety rules

- Do not drop a product because the price is blank, the price is `По запросу`, or the image is missing.
- Do not treat a blank price as zero.
- Do not publish Hilook discount notes or use 60 or 100 in place of the `Цена` amounts.
- Do not change EZVIZ data while applying a Hikvision-only job, or the reverse.
- Do not treat a missing file as deletion.
- Do not execute macros or write back into the workbook.
- Do not require a person or a model to interpret each cell. The rules above are the classifier. Uncertain identity and ambiguous images are flagged by those rules, not guessed.
