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

1. Reject the call unless status is `preview`. Phase 4B also returns the stored result when status is already `applied`.
2. Begin one database transaction and lock the job row.
3. Phase 4B does not persist `applying`. Approval is recorded on the same commit that sets `applied`, because `approved_by` is forbidden while the job is still `preview`. The `applying` value remains in the schema and is unused by this path.
4. For each included valid file, and for no other source:
   - Insert accepted brands and categories.
   - Insert new products, Russian translations, public USD prices, and source records. Locks are false. Stock is `in_stock`. Slug is allocated once. `catalog_status` follows the job’s publish choice for new rows (default published for a first load, visible in the preview).
   - Update matched products according to resolutions. Always refresh that source snapshot, `last_job_id`, and `last_seen_at`.
   - Link approved images. Skip checksums the product already has. Do not delete images the file no longer contains and do not delete administrator-uploaded images.
   - Mark this source’s mappings that were not in the file `absent_from_latest`. Do not archive them and do not change the other source’s flag.
5. Write the summary and an audit-log row.
6. Commit and set status `applied`.

An unexpected error rolls the transaction back and then sets `failed` with a generic `error_message`. Live catalog tables match the pre-apply state. A blocking validation or unresolved conflict returns an error and leaves the job in `preview` so it can be corrected.

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

## Phase 4A staging behavior

Phase 4A parses and stages. It does not upload over HTTP, preview in a UI, approve, or apply. Live `products` rows are not updated.

`stage_import` accepts an existing `preview` job and one or two workbook paths. Parsing, image extraction, matching, and database writes are separate functions. The caller commits. A failed flush deletes partial files and that job’s workbook copy. It does not delete checksum objects, because another job or product may share the hash, including a job that has not committed yet.

Identification follows the signature rules above. A filename that disagrees with the signature is reported on `import_jobs.summary.rejected_files` and does not create an `import_files` row, because storing it under either source would choose a side before confirmation. `admin_confirmed` with the required columns stages that declared source. An unreadable container is reported the same way and is not parsed.

A sheet without the required headers is an error on that sheet. Other sheets in the same workbook are still staged. Rows after the last value or image anchor are counted as `trailing_empty_rows` and are not inserted. Blank rows inside that span are staged as `blank`.

The match key is the unit-separator join of source code, worksheet name, case-folded model, case-folded option, and the SHA-256 of the trimmed description. Unicode dashes are folded to `-` in that key only. The display model keeps the original dash. Staging the same job again deletes that source’s staged rows and assets and inserts the new result. It does not insert a second file for the same source and does not write the live catalog.

Brand for an EZVIZ file is `EZVIZ`. A Hikvision brand is set only when the model or description text contains HiLook, Hikvision, Seagate, WD, Andel, or Cougar. The worksheet name is not a brand. No match, or more than one match, leaves the brand null and adds `brand_unverified` or `brand_ambiguous`.

Image bytes are read from the xlsx package. They are not decoded through Pillow, so the stored checksum is the embedded file. PNG, JPEG, and WebP are accepted after a content check. The same checksum is written once under `objects/{sha256[0:2]}/{sha256}.{ext}`. Anchors on a heading or other non-model row stay `unassigned` even when the drawing extends into the next row. A merged `Фото` range adds `shared_candidate` asset rows for the extra model rows and does not copy the file.

On 2026-10-10 a read-only pass of the local workbooks matched the measured population: 639 model rows, 28 Hilook headings, 3 stray rows, 587 numeric prices, 42 explicit `По запросу` cells, and 10 blank prices. Embedded image anchors totaled 762. Hilook has 20 anchors whose top-left cell is a heading, so those stay unassigned; the analysis note of 7 non-product Hilook images is not reproduced by the top-left rule. Both workbook SHA-256 values were unchanged by the pass. The pass did not write the catalog.

## Phase 4B upload, review, and apply

Phase 4B adds the HTTP workflow on top of `stage_import` and does not add a migration.

### Endpoints

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/admin/imports` | `require_admin_write` | Upload one or both workbooks and stage one preview job |
| `GET` | `/api/admin/imports/{job_id}` | `require_admin` | Combined preview, file validation, and rejected uploads |
| `GET` | `/api/admin/imports/{job_id}/rows` | `require_admin` | Paginated staged rows |
| `GET` | `/api/admin/imports/{job_id}/assets` | `require_admin` | Paginated staged images |
| `PATCH` | `/api/admin/imports/{job_id}/rows/{row_id}` | `require_admin_write` | Resolve or exclude one row in that job |
| `POST` | `/api/admin/imports/{job_id}/assets/{asset_id}/exclusion` | `require_admin_write` | Exclude or restore one staged image |
| `POST` | `/api/admin/imports/{job_id}/apply` | `require_admin_write` | Apply the job once when `confirm` is true |
| `POST` | `/api/admin/imports/{job_id}/reject` | `require_admin_write` | Reject a preview job |

`page` starts at 1. `page_size` defaults to 50 and cannot exceed 100. Row lists can be filtered by `source_code` and `action`.

### Upload limits and storage

`IMPORT_MAX_BYTES` defaults to 41943040. Settings reject a value below 1024 or above 41943040. Each request accepts at most two files. Bytes are counted while streaming. A file over the limit is rejected with 413 and is not parsed. The client filename is stored only as a display name. The temporary file uses a random name under `media/private-uploads/` and is deleted when the request finishes.

The workbook is identified from its sheets and headers. A filename that disagrees with that signature is returned in `rejected_files` with code `filename_signature_disagreement` and is not staged. Sending `source_overrides` of `hikvision` or `ezviz` for that file is the administrator confirmation. Macros are not executed. Zip entries that escape the workbook are rejected by the Phase 4A container check. Responses do not include server paths or parser tracebacks.

A staged workbook copy is `imports/{job_id}/{source}.xlsx`. Image bytes are `objects/{sha256[0:2]}/{sha256}.{ext}`. Nginx publishes `/media/objects/` only. `/media/imports/` and `/media/private-uploads/` return 404. The running Compose Nginx process is not reloaded by this change; the file in `deploy/nginx.conf` is what a later recreate will use.

### State transitions

- `preview` to `applied`: apply succeeded. `approved_by` and `applied_at` are set in that commit.
- `preview` to `rejected`: reject. `approved_by` stays null.
- `preview` to `failed`: an unexpected error during apply. The catalog transaction is rolled back first, then the failure is saved. `error_message` is the generic sentence `The import could not be applied.`
- `applied` to `applied`: a repeated apply returns the stored summary and does not insert again.
- `rejected` and `failed` cannot be edited or applied.
- Unresolved blocking rows return 409 and leave the job in `preview`.

Blocking rows are invalid rows that are not excluded, and `insert`, `update`, `possible_match`, or `conflict` rows whose resolution is still `pending`. An accepted update or possible match without a matched product is also blocking. Parsing does not approve the job. New rows default to `accept_new`, and unlocked exact matches default to `accept_excel`, but those rows are written only when an administrator posts apply.

### Conflict resolution

A row id is accepted only when its file belongs to the job in the URL. `keep_current` preserves the live values. `accept_excel` changes every `keep_current` field resolution on that row to `accept_excel`; that is the explicit override of a locked price, description, option, brand, category, or display model. `exclude` removes the row from apply and can be reversed while the job is still `preview`. A conflict cannot be resolved with `accept_excel` or `accept_new`. Heading, blank, and stray rows cannot be turned into products.

Possible matches stay `pending`. The matcher records the same field differences and lock defaults as an update, then forces the action back to `possible_match`. Choosing `keep_current` does not change the product and does not mark it absent. Choosing `accept_excel` updates the matched product and replaces its match key. Similar model names are not merged.

Asset exclusion is a list of asset ids on `import_jobs.summary.excluded_asset_ids`. Re-staging the same job replaces the summary, so exclusions belong to the job created by the upload.

### Catalog application and retries

Apply takes `SELECT … FOR UPDATE` on the job. A second request waits. If the first commit set `applied`, the second returns that result. If the first rolled back and marked `failed`, the second does not apply.

Only included, valid, non-pending rows are written. Inserts create the product, the Russian source translation, and the source record. Updates write a field only when its resolution accepts Excel. Hidden public prices are not overwritten. Stock, slug, product kind, catalog status of existing products, and Uzbek or English translations are not changed. New products use `in_stock`. `publish_new_products` selects `published` or `draft` for those new products. `replace_prices` is honored only when staging already marked the locked price `accept_excel` because the job option was set before preview.

Numeric public amounts are quantized to `0.01` USD. Blank and explicit `По запросу` both become public `on_request` with a null amount, and the source kind stays `blank` or `explicit_on_request`. Source snapshots, `last_job_id`, and `last_seen_at` are refreshed for touched products. Products of an included source that were not touched are marked `absent_from_latest` and are not archived or deleted. A source that was not in the job is not examined.

Only `linked_high` images that are not excluded, whose file exists under the media root, and whose checksum is not already on the product are inserted. The first of those is primary only when the product has no primary image. Missing image files are skipped. Existing product images are not deleted.

The audit row is `import_applied`. Its detail contains the result counts and the absent-product count. It does not contain passwords, tokens, or paths.

### Filesystem and database consistency

PostgreSQL and the disk are not one transaction.

- Checksum objects are written during staging, before any catalog reference is committed.
- The same checksum is not overwritten.
- Apply only inserts database rows that point at those keys.
- If apply rolls back, the catalog has no new references. The checksum files stay, because another job or product may share them.
- Staging deletes partial files and that job’s private workbook copy. It does not delete checksum objects. A later cleanup may remove a checksum only when neither `product_images` nor `import_assets` references it.
- An upload that stages no source removes that job’s `imports/{job_id}/` directory after the database rollback. Unreferenced checksums can remain and must be removed only by a later cleanup that checks `product_images` and `import_assets`.
- A retry after a timeout is safe when the first request committed: the job is `applied` and the second request does not create another product or image. If the first request never committed, the job is still `preview` or has been marked `failed`, and no catalog rows from that attempt remain.
