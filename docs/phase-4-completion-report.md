# Phase 4 — Excel import workflow

18 October 2026. The import system was already implemented. This pass audited it, fixed two confirmed defects, and verified the preview/apply boundary on a disposable database. No live catalog import was applied.

## Existing functionality

Parsing, staging, authenticated upload, conflict review, and one-shot apply were already in `api/app/importing/` and the admin screens at `/admin/imports`. No schema migration was added.

Already satisfied before this audit:

- One job accepts the Hikvision workbook, the EZVIZ workbook, or both. A second file for the same source is rejected before staging.
- Upload and preview write staging tables and private workbook copies. They do not change `products`.
- Apply is a separate authenticated action and requires `{"confirm": true}`.
- Locked prices stay unless the job set `replace_prices` or that price field is accepted on its own. Row-level Accept Excel does not flip other `keep_current` fields.
- A locked description stays until that field is accepted. Uzbek and English are never written from the workbook.
- An empty brand cell stays `keep_current` with `brand_absent`. It does not clear the assigned brand unless that field is accepted explicitly.
- Category lookup reuses a category when the Russian title matches after case-folding and collapsed whitespace, on the same parent, source, and worksheet.
- A changed Russian description is flagged `manual_translations_stale` when a non-empty manual Uzbek or English description exists. Those translations are kept.
- Blank prices and explicit `По запросу` both propose public `on_request` with a null amount. The source kind stays `blank` or `explicit_on_request`.
- Photo-column anchors on a model row are `linked_high` and can be linked. Other columns stay `linked_review`. Non-model anchors stay `unassigned`. A merged photo range adds `shared_candidate` rows and does not copy the file.
- Import jobs, files, rows, assets, source records, and an `import_applied` audit row record the history.
- A failed apply rolls the catalog transaction back and then marks the job `failed`. A rejected job cannot be applied. The original files in `data/source/` are not written.

## Defects fixed

1. Two incoming rows with the same match key were conflicts, but the existing product for that key was treated as missing. After the conflicts were excluded, apply set `absent_from_latest`. The product was in the file. Matching now records `ambiguous_product_ids`. Apply does not mark those products absent, and it clears a previous absence flag without changing the public price, description, brand, or category.
2. The review button “accept only this field” was shown on an excluded row. The API treated that request as restoring the row. An excluded row now returns 409 for a field override, and the button is hidden while the row is excluded.

`api/tests/__init__.py` marks the local test directory as a package so it is not hidden by another installed `tests` package.

## Tests

Disposable Postgres `cs-pytest-pg` on `127.0.0.1:55432`, not the Compose catalog. The container was removed after each run. The tests created and dropped their own databases.

| Command | Result |
| --- | --- |
| `pytest` of the four import modules, before the image rebuild | 50 passed in 26.37s |
| `npm run typecheck` in `web/` | Passed |
| `node --experimental-strip-types --test` on `web/src/lib/*.test.mts` | 27 passed |
| `pytest tests/test_import_api.py tests/test_import_stage.py` after the image rebuild | 31 passed in 21.34s |
| `pytest tests/test_import_parse.py tests/test_import_schema.py` after the image rebuild | 19 passed in 4.96s |

The second pair is the same 50 tests, run again on a new disposable database after the images were built. They did not use the Compose catalog.

The new API cases prove three boundaries:

- Uploading a duplicate-key workbook leaves the published price and the absence flag unchanged. Apply after excluding both conflicts still leaves the price unchanged, does not insert a product, and clears the absence flag.
- Excluding a changed row and then accepting one field returns 409. Apply keeps the original description and price.
- Two Hikvision files in one request return 422. No job and no product remain.

Existing cases still cover preview without apply, rollback of a failed apply, a repeated apply, locked fields, empty brands, stale translations, and category-name folding.

## Preview versus apply

Preview of the duplicate workbook returned HTTP 200 and staged two `conflict` rows. Before apply, the product price was still `77.00` and `absent_from_latest` was still true. Apply changed only the absence flag. It did not change the public product.

The two-file rejection and the excluded-field rejection also left the catalog without a partial publish.

## Live catalog

Before and after the image rebuild, `GET /api/health` on port 8080 returned `{"status":"ok","database":"ok"}`. `GET /api/public/products` still reported total 639. No workbook was uploaded or applied to that catalog. Administrator credentials, Docker volumes, and `data/source/` were not modified.

## Docker rebuild — 18 October 2026

`docker compose --env-file .env -f docker-compose.yml -f docker-compose.dev.yml up -d --no-deps --build api web` rebuilt and recreated only `camera-shop-api-1` and `camera-shop-web-1`. Postgres stayed container `747524f4819c`. Nginx stayed container `d2b45c32481e`. Volumes `camera-shop_postgres_data` and `camera-shop_catalog_media` were not removed. Nginx reached the new containers without a reload.

Checked on port 8080:

- Health returned ok and the database check returned ok.
- The public catalog total stayed 639.
- `GET` and `POST /api/admin/imports`, and `POST /api/admin/imports/1/apply` with `{"confirm":false}`, returned 401 `Authentication is required.` without a session.
- Opening `http://127.0.0.1:8080/admin/imports` in the browser redirected to `/admin/login`. No administrator session was present, so the upload form was not submitted and no workbook was previewed through the browser.

Checked inside the new images, not by writing the catalog:

- The API image contains `ambiguous_product_ids` and `An excluded row cannot override one field.`
- The web image’s import pages contain `hikvisionFile`, `ezvizFile`, `replacePrices`, `publishNew`, and `confirmApply`. The review page keeps the field button off when the row action is `exclude`.

The signed-in import screen was not exercised. There was no existing admin session, and the password was not read or reset. Pending on port 8080 until an administrator signs in: choosing one Hikvision file, one EZVIZ file, or both; a preview that leaves published products unchanged; and the on-screen conflict, locked-field, and apply-confirmation controls. Those behaviors are covered by the isolated API tests.

## Remaining limitations

- The signed-in import screen on port 8080 was not opened. Anonymous requests are rejected, and the rebuilt pages contain the upload and review controls.
- A matched apply still copies the workbook description into `source_description_raw` when the public description is kept.
- Products 186, 398, 399, and 454 still have unlocked Russian descriptions. A later cell change is accepted by default. Uzbek and English are flagged and kept.
- Accepting one field still writes that field. That is the explicit approval.
- An explicit brand-field approval can still clear an empty brand cell.
- `linked_review`, `unassigned`, and `shared_candidate` images are not attached. Rejected workbook drawings stay unattached.
- Product 18 stays unverified.
- Phase 3 is not complete: an existing administrator has not signed in and out on port 8080.
- Port 3010 is still the stale preview whose production files were overwritten by the dev server.

## Completion

The isolated import lifecycle and the preview/apply boundary are verified, and the API and web images on port 8080 now contain the fixes. No live workbook was uploaded or applied. Phase 3 remains open until an existing administrator signs in and out on port 8080.
