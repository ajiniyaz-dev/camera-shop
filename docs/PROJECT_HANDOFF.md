# Project handoff

Handoff for a new implementation chat. The nine specification documents in `docs/` are authoritative. If this summary disagrees with any of them, follow the specification.

Do not modify `data/source/`. Do not invent a domain, phone, email, address, or social URL.

## Objective and stack

Build a production informational catalog for the company **HikVision**. It is not a store.

- Frontend: Next.js, TypeScript, Tailwind CSS, App Router
- Backend: FastAPI, Pydantic, SQLAlchemy 2
- Database: PostgreSQL, migrations through Alembic
- Deployment: Docker, Nginx, HTTPS, on the existing Ahost VPS
- Images on disk (or later object storage); paths and metadata in PostgreSQL
- Modular monolith. No microservices, Redis, Celery, Kafka, or Kubernetes
- No AI, Google Sheets, cart, checkout, payments, customer accounts, or orders

## Authoritative documents

| Document | Governs |
| --- | --- |
| `docs/project-requirements.md` | Business scope, confirmed decisions, non-requirements |
| `docs/architecture.md` | Frontend, backend, storage, request flows, deployment |
| `docs/database-design.md` | Tables, price states, translations, import jobs, visibility |
| `docs/excel-data-analysis.md` | Measured workbook structure and image findings |
| `docs/excel-to-database-mapping.md` | Source column to database field, including update locks |
| `docs/import-strategy.md` | Two-workbook import, staging, matching, approval, recovery |
| `docs/seo-strategy.md` | Locales, URLs, metadata, hreflang, sitemap, structured data |
| `docs/security-strategy.md` | Auth, public/admin separation, uploads, backups, operations |
| `docs/open-questions.md` | Only the decisions that are still open |

## Confirmed business rules

- Numeric prices are stored as USD decimals. Visitors see one UZS amount: Hikvision workbook `stored_usd * 12000 * 0.8`, EZVIZ workbook `stored_usd * 12000 * 0.9`. The workbook’s `source_code` selects the formula, not the brand. HiLook sheets use the Hikvision formula. There is no live exchange rate. Half-up rounding to a whole soʻm does not change results for the current two-decimal USD amounts.
- Show only that one price. Do not show the stored USD amount, the Hilook discount notes, or a discount badge.
- Explicit `По запросу` is the request-price state. A blank price is not zero; its public status also starts as that request-price state. Provenance still records that the source cell was blank.
- Public on-request labels, stored in `api/app/price_labels.py` rather than on product rows: Russian `По запросу`, Uzbek `So'rov asosida`, English `On request`.
- EZVIZ public prices start from `Цена для дилера`. Hikvision public prices start from `Цена`. The dealer column name is internal and must not appear on the public site.
- Public and admin UI: Russian (`ru`), Uzbek (`uz`, Latin), and English (`en`), under `/ru`, `/uz`, and `/en`. Do not present Russian source text as a verified Uzbek or English translation.
- Keep every legitimate product and category. Repeated model names stay separate, with their own ids and slugs. Do not merge them.
- Do not treat every row in the Hikvision workbook as a Hikvision product. Assign a brand only when the model or description identifies it. The worksheet name alone is not a brand. If the brand is unclear, import the product with a null brand and flag it.
- Show stock only when staff mark a product out of stock. No quantities. Do not infer stock from Excel. New products start in stock. Stock does not change the price state.

## Verified Excel findings

Source files, unmodified and kept out of Git:

- `data/source/Hikvision pr.xlsx`
- `data/source/Ezviz pr.xlsx`

On worksheet `Hilook`, these are cell values, not comments. Column F has no header. Display the column E price only. Keep the note internal.

| Note | Main price |
| --- | --- |
| `F103` `текущая цена со скидкой 60$` | `E103` = 115 USD |
| `F106` `текущая цена со скидкой 60$` | `E106` = 115 USD |
| `F107` `текущая цена со скидкой 100$` | `E107` = 200 USD |
| `F115` `текущая цена со скидкой 100$` | `E115` = 200 USD |

Do not re-analyze the workbooks unless a specification detail cannot be implemented as written. Counts, image-anchor rules, and column mappings are already in the analysis, mapping, and import documents.

## Excel import rules

Parsing, staging, authenticated upload, preview, conflict resolution, and apply are implemented. The admin review screen uses those routes and does not contain a second importer. One import job may contain the Hikvision file, the EZVIZ file, or both.

- Identify each file by headers and sheet structure. The filename is evidence, not proof.
- Never write one source’s rows into the other source.
- Uploading or previewing does not change the live catalog.
- Stage changes, then show one combined preview.
- One **Apply approved changes** action commits the approved rows for the files included in that job.
- A missing file, an invalid file, or a product absent from a file is not a delete. The other source stays as it is. Absent products are reported and kept until an administrator archives them.
- Re-importing an unchanged file must not duplicate products.
- Do not match on model name alone or on Excel row number alone. The match key is source, worksheet, normalized model, normalized option, and description hash.
- Manual edits to price, description, option, brand, category, and display model are kept unless the administrator accepts the Excel value. Replacing prices is an explicit batch option and must be visible in the preview before apply.
- Assign an embedded image only when the anchor evidence is high confidence. Keep ambiguous and unassigned images for review.

## Production and security requirements

From `docs/architecture.md` and `docs/security-strategy.md`. Not all of this is built yet.

- Public and admin responses use separate schemas. Discount notes, the EZVIZ header `Цена для дилера`, server paths, and import diagnostics are not public.
- Passwords are Argon2id hashes. Sessions are server-side. Admin operations check authentication on the server. State-changing admin requests also require CSRF.
- The first administrator is created by a one-off command. The password is not committed.
- PostgreSQL is on the Docker network only and is not published on the host in `docker-compose.yml`. `docker-compose.dev.yml` binds Postgres and Nginx to `127.0.0.1`.
- Nginx serves `/`, `/api/`, and `/media/` with directory listing off. TLS and HSTS wait until the client supplies the domain.
- Secrets come from the environment: `DATABASE_URL`, `SESSION_SECRET`, `MEDIA_ROOT`, `MEDIA_PUBLIC_BASE_URL`, `PUBLIC_SITE_URL`. `.env.example` holds placeholders only.
- Production runs with debug mode off and interactive API docs disabled. `APP_ENV=production` rejects a placeholder `SESSION_SECRET` and rejects `DEBUG=true`.
- Daily `pg_dump` and a media-volume copy are still deployment work, not application code.

## Remaining client details

Do not invent these. They are recorded in `docs/open-questions.md`.

- Exact domain. Canonicals use `PUBLIC_SITE_URL` until it is supplied. The repository default is `http://localhost`.
- Real phone, email, address, opening hours, and social URLs. The seeded profile leaves them null.
- Whether the displayed USD price should be described as including or excluding tax. The stored amount does not change either way.

## What is implemented

### Phase 1

Verified by the files in the repository and by the checks run while building them.

- `api/`: FastAPI, SQLAlchemy engine, Alembic configured, `GET /api/health` (process plus `SELECT 1`; 503 when the database is unreachable; docs disabled unless `DEBUG=true`).
- `web/`: Next.js, TypeScript, Tailwind, App Router, one development landing page titled “HikVision catalog”. Server-side API base URL is `API_INTERNAL_URL`.
- `docker-compose.yml`, `docker-compose.dev.yml`, `deploy/nginx.conf`.
- `.env.example` and `.gitignore`.

### Phase 2A

Verified by `api/app/models/` and Alembic revision `phase2a_core` in `api/alembic/versions/phase2a_core_schema.py`.

Tables:

- `brands`, `brand_translations`
- `categories`, `category_translations`
- `products`, `product_translations`
- `product_specifications`, `product_specification_translations`
- `product_images`
- `product_source_records`
- `business_profile`
- `admin_users`

Behavior encoded in that schema:

- Prices use `numeric(12,2)`, not floating point. Public currency is `USD` only when the status is `numeric`.
- `source_price_kind` is `numeric`, `explicit_on_request`, or `blank`. Blank and explicit request prices cannot store an amount. Both are initialized in the public columns as `on_request` with a null amount.
- `stock_status` defaults to `in_stock` and is independent of `public_price_status`.
- There is no unique constraint on model name, raw model, or normalized model. `slug` is unique. `product_source_records.match_key` is unique, and each product has at most one source row.
- Locales on translation rows are `ru`, `uz`, and `en`. Russian source text is the `ru` row. Uzbek and English are not filled from the workbook.
- `business_profile` is seeded with `id = 1` and `public_name = HikVision`. Contact fields, domain, social links, and logo are null. A check constraint allows only `id = 1`. That primary key is a fixed value, not a generated identity.
- `admin_users` exists for later authentication. There is no login route, no session table, and no seeded administrator.
- Image MIME values allowed by the check constraint are `image/png`, `image/jpeg`, and `image/webp`. One non-rejected primary image per product is enforced by a partial unique index.

### Phase 2B

Verified by `api/app/models/imports.py`, `api/app/models/audit.py`, and Alembic revision `phase2b_import` in `api/alembic/versions/phase2b_import_schema.py`. It revises `phase2a_core`. The Phase 2A migration file was not rewritten.

Tables added:

- `import_jobs` — one review and one apply. A job may contain the Hikvision file, the EZVIZ file, or both. Unique `(job_id, source_code)` on `import_files` keeps the sources independent. A missing file is the absence of that source’s row, not a delete.
- `import_files` — original filename, SHA-256, identification (`auto` or `admin_confirmed`), validation status, validation errors, stored object key, and `included_in_apply`. An invalid file must record at least one error and cannot be included in apply. A valid file may still be excluded.
- `import_rows` — staged worksheet rows. Classification, action, resolution, raw cells, proposal, messages, matched product, and applied flag. Unique `(import_file_id, worksheet_name, source_row)`. Pending `conflict` and `possible_match` rows cannot be marked applied. `accept_excel` on a row applies unlocked fields. A locked field changes only when that field’s own resolution is `accept_excel`. `replace_prices` on the job defaults to false.
- `import_assets` — extracted images, including `unassigned` and `shared_candidate`.
- `admin_audit_log` — `actor_id` is nullable so an unknown failed login can be recorded. Detail JSON cannot contain `password`, `password_hash`, `secret`, `session_token`, or `token` keys.

`publish_new_products` is `BOOLEAN NOT NULL DEFAULT TRUE` on `import_jobs`. Documented job statuses are `preview`, `rejected`, `applying`, `applied`, and `failed`. Those cover upload (the job and file rows), validation (`import_files.validation_status`), review (`preview` plus row resolution), applying, completed (`applied`), and failed. `applied` requires `applied_at`. `preview` and `rejected` cannot have `approved_by`.

`product_source_records.first_job_id` and `last_job_id` now reference `import_jobs` with `ON DELETE RESTRICT`. On upgrade, existing catalog rows are kept. Referenced job ids are backfilled as `applied` jobs when an administrator already exists. If source rows point at missing job ids and no administrator exists, the foreign keys are added `NOT VALID` and those source rows stay. Downgrade to `phase2a_core` drops the import tables and leaves the Phase 2A rows.

Not created in Phase 2B: `admin_sessions`, `slug_redirects`. No workbook parser, image extractor, import endpoint, CRUD API, authentication endpoint, admin UI, public page, or SEO output.

### Phase 3

Verified by `api/app/auth/`, `api/app/cli/create_admin.py`, and Alembic revision `phase3_admin_sessions` in `api/alembic/versions/phase3_admin_sessions.py`. It revises `phase2b_import`. The Phase 2A and Phase 2B migration files were not rewritten.

- `POST /api/auth/login` checks Argon2id, writes a generic failure, and on success sets cookies and returns `id`, `email`, `role`, and `csrf_token`.
- `POST /api/auth/logout` revokes the session when the CSRF token and origin match, then clears both cookies on the response that is returned. A missing or expired session still clears the cookies and returns 204. A failed CSRF check returns 403 and leaves the session in place.
- `GET /api/auth/me` returns `id`, `email`, and `role`, or 401.
- `require_admin` is the backend dependency for later authenticated reads. `require_admin_write` is the dependency for later state-changing admin routes: it requires an active administrator, the CSRF token, and a matching origin. A non-admin role returns 403. The schema still allows only `admin`.
- `admin_sessions` stores UUID `id`, `user_id` (`ON DELETE CASCADE`), HMAC digests `token_hash` and `csrf_token_hash`, `expires_at`, `revoked_at`, and `created_at`. Raw tokens are not stored.
- Session cookie `hikvision_session` is `HttpOnly`, `SameSite=Lax`, path `/api`. `Secure` is set only when `APP_ENV=production`. Default lifetime is 12 hours (`SESSION_TTL_SECONDS`).
- CSRF cookie `hikvision_csrf` is not `HttpOnly`, so the future admin UI can copy it into `X-CSRF-Token`. State-changing requests must send that header and a matching `Origin` or `Referer`. A new login rotates the token.
- Failed logins are limited in process: 10 per address per 15 minutes unless the environment overrides it. Counters are not shared across workers. `TRUST_PROXY=true` in Compose reads `X-Real-IP`.
- `python -m app.cli.create_admin [email]` prompts for the password and refuses to run when an administrator already exists. It does not accept `--password`.

### Phase 4A

Verified by `api/app/importing/` and `api/tests/test_import_parse.py`. No new Alembic revision. Phase 2A, Phase 2B, and Phase 3 migration files were not rewritten.

`stage_import` parses an existing preview job. It writes `import_files`, `import_rows`, `import_assets`, and `import_jobs.summary`. It does not create HTTP routes, change `products`, publish rows, or set `applied`.

- Hikvision and EZVIZ can be staged separately or together. Columns are found by header text.
- Blank prices stay `blank` and explicit `По запросу` stays `explicit_on_request`. Both propose public `on_request` with a null amount. Hilook column F stays `internal_note`.
- EZVIZ prices come from `Цена для дилера`. EZVIZ brand is `EZVIZ`. Hikvision brands come only from model and description text.
- Repeated models stay separate. The match key includes source, worksheet, normalized model, normalized option, and description SHA-256.
- Exact keys become `update` or `unchanged`. A unique model/option pair with a different description becomes `possible_match` and stays `pending`. Locked fields default to `keep_current` unless `replace_prices` selects the Excel price. None of those choices are applied in this phase.
- Images are copied by checksum. Photo-column anchors on a model row are `linked_high`. Other columns are `linked_review`. Non-model anchors are `unassigned`. Merged photo ranges add `shared_candidate` rows without a second file copy.
- Running the same job again replaces that source’s staged rows and assets.
- A filename/signature disagreement is stored on the job summary and does not create an `import_files` row until an administrator confirms the source.

A read-only pass of the local workbooks on 2026-10-10 counted 639 model rows, 28 headings, 3 stray rows, 587 numeric prices, 42 explicit request prices, 10 blank prices, and 762 image anchors. The workbook hashes were unchanged. Details and the Hilook heading-anchor difference are in `docs/import-strategy.md`.

### Phase 4B

Verified by `api/app/importing/router.py`, `api/app/importing/apply.py`, and `api/tests/test_import_api.py`. No new Alembic revision. The Phase 2A, Phase 2B, and Phase 3 migration files were not rewritten. The existing `import_jobs` check forbids `approved_by` while status is `preview` or `rejected`, so approval is the apply action itself.

Write routes use `require_admin_write`. Read routes use `require_admin`. Job responses omit workbook storage keys and absolute paths. A staged row proposal can include the relative image object key.

- `POST /api/admin/imports` accepts one or two `.xlsx` files, optional `source_overrides`, `replace_prices` (default false), and `publish_new_products` (default true). `IMPORT_MAX_BYTES` defaults to 41943040 and cannot be set above that ceiling. The minimum accepted setting is 1024. Uploads are streamed into `media/private-uploads/` under a random name, then staged. The temporary directory is removed after the request.
- `GET /api/admin/imports/{job_id}` returns the combined preview summary and source-file validation.
- `GET /api/admin/imports/{job_id}/rows` and `GET /api/admin/imports/{job_id}/assets` are paginated. `page_size` is at most 100.
- `PATCH /api/admin/imports/{job_id}/rows/{row_id}` sets `keep_current`, `accept_excel`, `accept_new`, or `exclude` on a row that belongs to that job. An optional `field` and `field_resolution` change one changed field and do not rewrite the others.
- `POST /api/admin/imports/{job_id}/assets/{asset_id}/exclusion` records an asset id in the job summary. There is no excluded column on `import_assets`.
- `POST /api/admin/imports/{job_id}/apply` with `{"confirm": true}` applies the job once.
- `POST /api/admin/imports/{job_id}/reject` sets `rejected` from `preview` only.

`preview` can become `applied`, `rejected`, or `failed`. A repeated apply of an `applied` job returns the stored result. A 409 for unresolved rows leaves the job in `preview`. An unexpected apply error rolls the catalog transaction back and then marks the job `failed`. This path does not persist `applying`, so there is no stuck-`applying` recovery step.

A possible match stays `pending` and blocks apply. Its field differences and lock defaults are stored on the row. `accept_excel` on the row does not overwrite fields that are still `keep_current`. Overwriting one locked field requires `field` and `field_resolution` `accept_excel`. A conflict cannot choose one Excel value. A row from another job is rejected. A missing workbook does not delete or flag the other source.

Apply locks the job row, writes only included valid rows, and commits the catalog changes with status `applied`, `approved_by`, and `applied_at` in one database transaction. New products start `in_stock`. `publish_new_products` chooses `published` or `draft` for new products only. Slugs are assigned once. USD amounts use two decimal places. Discount notes stay internal. Image rows point at checksum objects written during staging. A failed database transaction does not delete a checksum that another job or product might share. Nginx serves `/media/objects/` only.

### Phase 5

Verified by `api/app/catalog/router.py`, the admin routes under `web/src/app/admin/`, and the checks below. No new Alembic revision. The Phase 2A, Phase 2B, and Phase 3 migration files were not rewritten.

The admin UI is mounted at `/admin` and is `noindex`. Public `/ru`, `/uz`, and `/en` catalog routes are not part of this phase. The public page remains the Phase 1 placeholder. Russian is the default admin language. Uzbek Latin and English are switched with `POST /admin/locale`, which sets the non-HttpOnly cookie `hikvision_ui_locale` (path `/`) and redirects only to a path that starts with `/admin`. Switching language is a full navigation, so unsaved form text is discarded.

Authentication stays on the Phase 3 session. `hikvision_session` remains `HttpOnly`, `SameSite=Lax`, path `/api`. `hikvision_csrf` is not `HttpOnly` and its path is `/`, so script on `/admin` can copy it into `X-CSRF-Token`. Every catalog and import write uses `require_admin_write`. Reads use `require_admin`. The browser client does not store the session in `localStorage` or `sessionStorage`. A 401 from an admin request sends the browser to `/admin/login`. The Next.js layout asks `GET /api/auth/me` before showing the panel; the API remains the authorization check.

Screens:

- `/admin/login` — email and password
- `/admin` — dashboard counts from `GET /api/admin/dashboard`
- `/admin/products`, `/admin/products/new`, `/admin/products/[id]` — list, search, brand and category filters, sort, pagination, create, edit, archive, specifications, images
- `/admin/brands` and `/admin/categories` — create and edit, including translations, brand description, and category parent
- `/admin/imports` and `/admin/imports/[id]` — upload, preview, row review, asset pages, apply, reject
- `/admin/profile` — the single company profile

Catalog routes, all under `/api/admin`:

- `GET /dashboard`
- `GET` and `POST /products`; `GET` and `PATCH /products/{id}`; `POST /products/{id}/archive` with `{"confirm": true}`
- `POST /products/{id}/images`; `PATCH` and `DELETE /products/{id}/images/{image_id}`
- `GET` and `POST /brands`; `PATCH /brands/{id}`
- `GET` and `POST /categories`; `PATCH /categories/{id}`
- `GET` and `PATCH /profile`

Products are archived, not hard-deleted. Brands and categories have no delete route. A manual product starts as `draft`, public price `on_request` with a null amount, and stock `in_stock`. A numeric price requires a non-negative USD amount with at most two decimal places. `on_request` rejects a supplied amount. Stock can change without changing the price. The first uploaded image is primary. Another image can be marked primary. Deleting an image removes the row and promotes another primary when needed; it does not delete the stored file. Supplied manual fields are locked. A later edit locks a field only when that field changes. Audit actions include `product_created`, `product_updated`, `product_price_changed`, `product_archived`, `image_added`, `image_updated`, `image_removed`, `brand_created`, `brand_updated`, `category_created`, `category_updated`, and `profile_updated`.

`GET /api/admin/imports` lists recent jobs. Import row responses now include `current` when the row is matched to a product: display model, option, Russian brand and category names, Russian description, public price, and lock flags. Asset responses include `anchor_model` when a staged row shares the file, worksheet, and anchor row. The review screen shows the worksheet, classification, action, resolution, message codes, exclusion, and the incoming price, brand, category, and description. When `field_changes` is present it shows the current value, the incoming value, and the field resolution. A locked public price is called out with both amounts. Choosing `accept_excel` asks for confirmation and names the fields that stay `keep_current`. Each of those fields has its own confirmation before it can be accepted. `brand_absent` and `manual_translations_stale` are explained in the review. Conflicts can be kept or excluded; they cannot take `accept_excel`. Apply is offered only while the job is `preview`, and only after the confirmation checkbox. A failed apply, including HTTP 409, leaves the status unchanged. `replace_prices` stays an upload option and does not bypass the row rules.

The asset list requests `page` and `page_size` (the API maximum is 100; the screen uses 20) and shows link status, worksheet, anchor row, and anchor model. Only `linked_high` images that are not excluded are published by apply. Review, unassigned, and shared-candidate images stay staged.

`web/next.config.ts` rewrites `/api/:path*` to `API_INTERNAL_URL` when that variable is set. Next.js development does not serve `/media/objects/`. Production Nginx still serves that prefix.

### Test result

On 2026-10-10, `pytest -q` from `api/` reported **74 passed** and 1 Starlette deprecation warning. That run includes the Phase 2A, Phase 2B, and Phase 3 regression tests, their upgrade and downgrade checks, the Phase 4A parser and staging tests, the Phase 4B upload, resolution, and apply tests, and the read-only source-workbook check. An earlier run the same day, before the import API existed, reported 64 passed. A review pass then fixed conflict restoration, zip-path rejection, and checksum cleanup; the 74-pass run includes those fixes.

The tests did not use the Compose `catalog` database. A disposable PostgreSQL 16 container was published on `127.0.0.1:55432`. The tests created and then dropped `catalog_phase4b_test`. The disposable container was removed afterward. The Compose database was not migrated and was not dropped.

On 2026-10-10, after the Phase 5 catalog and import-review changes, `pytest -q --tb=short` from `api/` reported **78 passed, 0 failed, 0 skipped, 0 errors**, and the same Starlette deprecation warning. `PHASE2A_ADMIN_URL` pointed at a disposable cluster on `127.0.0.1:55432`. The suite created and dropped its own named test databases. It did not use the Compose catalog database or the host PostgreSQL service on port 5432. Docker was not running.

The same command was run again after the failed-apply screen fix, against that same disposable cluster. Preflight showed database `postgres` on port `55432`, plus the browser database `catalog_phase5_harden`. Result: **78 passed, 0 failed, 0 skipped, 0 errors**, in 38.22s, with one Starlette deprecation warning (`httpx` via `starlette.testclient`). `npm run typecheck` exited 0 after that fix. `npm run build` exited 0 on Next.js 15.5.27 after the dev server was stopped. `/` is static and every `/admin` route is dynamic. There is no lint script and no frontend test runner.

Browser checks used that same disposable cluster, database `catalog_phase5_browser`, API `127.0.0.1:8000`, and Next.js `http://localhost:3000`. The administrator was the test account `admin@example.com`. The Compose catalog was not migrated, imported, or dropped.

Checked in the browser:

- Logged-out visits to `/admin` and `/admin/products` reached `/admin/login`.
- Login and logout. Logout returned to the login screen.
- Russian, Uzbek Latin, and English on the signed-in dashboard, with translated navigation.
- Dashboard counts from the API: 2 products, 1 published, 1 draft, 0 archived, 1 brand, 2 categories, 0 conflicts, 0 invalid files, and the three import jobs with statuses rejected, applied, and rejected.
- A product was created and edited. Numeric price `92.50` replaced `on_request`. Stock was set to `out_of_stock` without changing that price.
- One image uploaded as primary, a second image uploaded, primary switched, and one image removed.
- A brand, a category, and the company profile were saved. The profile phone was a disposable test value and was cleared again. No production contact was invented.
- A generated Hikvision workbook previewed as an insert. Apply with the confirmation checkbox returned status `applied` and created the product. A second upload of the same workbook, after the imported price was edited to `55.00`, showed a locked-price warning (`numeric 55.00` versus incoming `numeric 40.00 USD`) and a confirmation that named the price field.
- A generated duplicate-model workbook stayed `preview` after apply and showed `Resolve blocking rows before applying this import.` Two conflict jobs were rejected. An applied job stayed `applied`. A file named like EZVIZ but structured as Hikvision stayed on the upload screen with `The workbook could not be staged.`

A later hardening pass used a new disposable database, `catalog_phase5_harden`, on the same kind of temporary cluster (`127.0.0.1:55432`). Docker and Nginx were not available, so production `deploy/nginx.conf` was not changed. A local stand-in on `127.0.0.1:8080` applied the same public-object rule: only a file under `media/objects/` is returned, and `/media/imports/`, `/media/private-uploads/`, directory listings, missing files, and `..` paths return 404. The admin UI was opened through that stand-in so image tags could load. Next.js development still does not serve `/media/objects/` by itself.

Checked in that pass:

- Logged-out `/admin/products` reached `/admin/login`. Login succeeded. `document.cookie` contained `hikvision_csrf` and not `hikvision_session`. `localStorage` and `sessionStorage` were empty. `GET /api/admin/dashboard` without cookies returned 401. A write without `X-CSRF-Token` returned 403.
- Two product images rendered (`naturalWidth` 1) from `/media/objects/{hash}.png`. Primary selection and deletion still worked. Cancelling image removal left both images.
- Archive asked `Архивировать этот товар? Он останется в базе и не будет удалён.` Cancelling left the product `draft`. Confirming set `archived` without changing `on_request` or `in_stock`. The product list filter showed `HARDEN-1`, `on_request`, `in_stock`, `archived`.
- A generated workbook showed a blank price as `on_request (blank)`, explicit `По запросу` as `on_request (explicit_on_request)`, and the Hilook discount note as an internal note beside the public price `115.00 USD`.
- A generated workbook with 105 images paged the asset list `1 / 6` through `6 / 6`. The API returned 105 distinct ids, 20 per page and 5 on the last page, in id order. Excluding `Hikvision CAM-101` on page 6 stayed on page 6 and persisted `excluded: true`.
- Unresolved conflicts blocked apply and stayed `preview`. The conflict buttons did not offer `accept_excel`. Excluding a conflict and then sending `accept_excel` returned 409, `A conflicting row cannot choose one Excel value.`
- A disposable preview whose staged amount was not a number returned `The import could not be applied.`, left the catalog unchanged, and stored status `failed`. The screen now reloads after a failed apply, so the heading becomes `failed`, the failure text stays visible, and Apply is hidden. Repeating apply returned 409. A later upload of a valid workbook still applied.
- Applying one valid row inserted one product. Applying that same job again returned the stored result and left the catalog at two products.

Audit rows on that disposable database included `product_created`, `image_added`, `image_updated`, `image_removed`, `product_archived`, and `import_applied`.

The earlier browser session had already covered language switching, dashboard counts, numeric versus `on_request` editing, stock independent of price, brand and category editing, profile save and clear, and the locked-price confirmation. Those screens were not rebuilt in this pass. Logout was not repeated.

### Phase 6

The public catalog is a server-rendered Next.js App Router site in Russian, Uzbek Latin, and English. `/` redirects to `/ru`. Unknown locales use the root not-found page. Administrator routes stay under `/admin` and are not linked from the public header.

Public pages:

- `/{locale}` homepage: company name, search, published category cards with subtree product counts, up to eight newest published products, and only the company fields that are filled in
- `/{locale}/catalog` and `/{locale}/products`: the same listing
- `/{locale}/search?q=`
- `/{locale}/categories`, `/{locale}/categories/{slug}` for a root, and `/{locale}/categories/{slug}/{child}` for a child
- `/{locale}/products/{product-slug}`
- `/{locale}/brands/{brand-slug}`
- `/{locale}/contact`

The language switch keeps the current path and query. Interface copy is in `web/src/lib/public-i18n.ts`. A missing Uzbek or English product, category, brand, or specification value falls back to the Russian text and the page says that the Russian original is shown. A missing name uses `model_display` and is not labeled as a translation. There is no frontend test runner and no lint script in `web/package.json`.

Public API, prefix `/api/public`, no administrator session:

- `GET /home`, `GET /company`, `GET /categories`, `GET /categories/{slug}`, `GET /categories/{parent}/{slug}`
- `GET /brands/{slug}`
- `GET /products` with `locale`, `q`, `category`, `parent`, `brand`, `min_price`, `max_price`, `sort`, `page`, `page_size`
- `GET /products/{slug}`

Responses are explicit dictionaries. They do not include source rows, locks, audit data, dealer column names, import notes, private object keys, or checksums. Phase 6 omitted SEO fields. Phase 7 adds `seo_title` and `seo_description` on product, category, and brand detail for the requested locale only, with no Russian fallback. Publication filtering is in the query: `catalog_status = published` and `deleted_at IS NULL`. Draft, archived, and deleted products return 404 from the detail route. An unpublished brand or category is omitted from the product; the product stays listable. Images are `high` or `confirmed` only, primary first, at `/media/{object_key}`.

Search is bounded `ILIKE` on the display model, normalized model, option, and translation name or description. It does not use `search_vector`. Category filters include published descendants. Price bounds apply only to `numeric` USD rows, so `on_request` and `hidden` are excluded when a bound is set. `hidden` is returned without an amount. Sort values are `model`, `name`, `newest`, `price_asc`, and `price_desc`, with the id as a tie-break. Numeric price sorts put null amounts last and do not treat them as zero. `page` is at least 1 and `page_size` is 1–48, default 24. Public responses send `Cache-Control: no-store`.

On-request labels stay in `api/app/price_labels.py`: Russian `По запросу`, Uzbek `So'rov asosida`, English `On request`. Numeric public prices render as Uzbek soʻm from the workbook UZS formula (stored USD unchanged). Out of stock is shown only when `stock_status` is `out_of_stock`. In stock shows no badge and no quantity.

No Alembic revision was added.

Verification on this machine:

- `pytest -q --tb=short` from `api/`: 83 passed, 1 warning (`StarletteDeprecationWarning` for httpx). The database was a temporary PostgreSQL 18 cluster on `127.0.0.1:55432`, database `catalog_phase6_test`, created and dropped by the test fixture. `PHASE2A_ADMIN_URL` pointed at that cluster. The Compose catalog and the host PostgreSQL service on port 5432 were not migrated or dropped.
- `npm run typecheck` passed.
- `npm run build` passed. Public routes are dynamic. There is no lint script.
- Browser checks used disposable database `catalog_phase6_browser` on the same temporary cluster. Docker and Nginx were not running. Next.js development does not serve `/media/objects/`. A local stand-in on `127.0.0.1:18080` forwarded the site to Next and the API, and served only files under `media/objects/`. Port 8080 could not be bound on this Windows machine. A private `/media/` path returned 404. Product images loaded with `naturalWidth` 1 from `/media/objects/bb/primary.png` and `/media/objects/cc/second.png`. A `needs_review` image was not shown.

Browser workflows that completed:

- Russian, Uzbek, and English homepages, including the language switch from `/ru` to `/en` and a direct `/uz/products/cam-pub` URL.
- Category cards, the empty category `Пустая полка` with count 0, and `/ru/categories/cameras/domes` showing only the child product.
- Header search for `ITEM-01` returned one result. Catalog filters `min_price=20` and `sort=price_asc` returned seven numeric prices from `$20.00` through `$92.50`, with on-request and hidden rows excluded.
- Page 2 of the catalog showed one product and Previous returned to 24 products on page 1.
- Product detail showed the English name, `$92.50`, description, Russian specification with the fallback label, and two images. The Uzbek on-request product showed `So'rov asosida` and `Mavjud emas`, and no zero price.
- `/ru/products/draft-secret` rendered the not-found state. Direct API checks returned 404 for the draft and archived slugs.
- At a 390px width the menu control was visible and the product card fit the viewport. At 768px the desktop navigation was shown.
- Admin login, `/admin/products`, and `/admin/imports` still opened. The product list still showed the draft and the archived rows that the public catalog hides.

A segment `loading.tsx` made `notFound()` respond with HTTP 200, so the locale segment does not use one. Invalid products and categories still render the not-found copy, and the product and archived routes returned HTTP 404 when requested from Next directly.

### Phase 7

Public pages now have server-rendered titles, descriptions, robots directives, Open Graph, and Twitter card metadata. Product and category copy comes from the published catalog. A locale `seo_title` or `seo_description` is used only when that locale has one. A missing Uzbek or English description does not become the Russian sentence in the meta description. The fallback is the brand, when published, the model, the option label, and the category name. `html lang` stays `ru`, `uz`, or `en`.

`PUBLIC_SITE_URL` is the public origin. `http://localhost`, `127.0.0.1`, and `::1` are placeholders. With a placeholder, canonical links, hreflang, absolute Open Graph URLs, sitemap hosts, and JSON-LD site URLs are omitted. With a non-loopback origin, those URLs use that origin. The web container receives the same variable. No production domain was invented.

Indexable URLs are the locale home, catalog, category index, contact, published category and brand pages, and published products. Search, filters, sort, and page 2 and later are `noindex, follow` and canonical to their own URL. `/{locale}/products` is `noindex` and canonical to `/{locale}/catalog`. The sitemap does not list those variants.

`/sitemap.xml` is generated by Next.js from `GET /api/public/sitemap`. Entries are the three locales of home, catalog, the category index, contact, published categories, published brands, and published products. Draft, archived, deleted, unpublished brands and categories, admin, API, and search URLs are absent. `lastmod` comes from `updated_at` on products, categories, and brands. The static pages omit it. Alternates include `ru`, `uz`, `en`, and `x-default` for Russian.

`/robots.txt` allows `/ru`, `/uz`, and `/en`, and disallows `/admin`, `/api/`, `/media/imports`, and `/media/private-uploads`. The Sitemap line is present only when the public origin is configured. `robots.txt` is not access control.

JSON-LD on a published product is `Product` plus `BreadcrumbList`. `sku` is the slug. `Offer` is included only for a numeric public price and uses the displayed soʻm amount with `priceCurrency` `UZS` (not the stored USD amount). `availability` is `OutOfStock` only when that product also has a numeric price and staff marked it out of stock. In stock, `on_request`, and `hidden` do not invent availability. There is no rating or review. The homepage and contact page use `Organization`, or `LocalBusiness` when an address is saved. `WebSite` and `SearchAction` are on the homepage only when the origin is configured, and the target is `/{locale}/search?q={search_term_string}`. Breadcrumbs on category, brand, and product pages match the visible trail. Image and logo URLs are absolute only when the origin is configured and the public image exists.

Product `<title>` generation (after the multilingual SEO polish) prefers the locale’s `seo_title`, otherwise the localized name (or display model), then a distinct manufacturer only when it differs from the site name, then `| HikVision`. Missing or Hikvision-cased brands do not repeat as `Name — HikVision | HikVision`.

Slugs stay as assigned at insert. The admin API does not change a product, brand, or category slug, so `slug_redirects` was not added and no migration was added. An unknown or unpublished slug still returns HTTP 404. `search_vector` is still unused.

These checks show that the tags and sitemap are generated. They are not a Google Search Console or Bing Webmaster validation.

Verification on this machine:

- `pytest -q --tb=short` from `api/`: 84 passed, 1 warning (`StarletteDeprecationWarning` for httpx). The database was a temporary PostgreSQL 18 cluster on `127.0.0.1:55432`. The public-catalog fixture used `catalog_phase7_test` and dropped it. `PHASE2A_ADMIN_URL` pointed at that cluster. The Compose catalog and the host PostgreSQL service on port 5432 were not migrated or dropped.
- `npm run typecheck` passed.
- `npm run build` passed. `/sitemap.xml` and `/robots.txt` are dynamic. There is no lint script.
- HTTP checks used disposable database `catalog_phase7_browser` on the same temporary cluster, with the API on `127.0.0.1:8000` and `next start` on `127.0.0.1:3000`. With `PUBLIC_SITE_URL=http://catalog.example`, `/ru`, `/uz`, and `/en` returned 200 with titles, canonicals, hreflang including `x-default`, and Open Graph. `/ru/products/child-cam` used the model title, the primary image as `og:image`, a numeric offer, and no rating. **Historical note (Phase 7 fixture run):** that disposable check recorded a USD offer before public display and JSON-LD switched to UZS; current code emits `priceCurrency` `UZS` for numeric offers. `/uz/products/child-cam` did not put the Russian description in the meta description. `/ru/products/request-cam` had no offer. Filtered catalog and search URLs were `noindex` and canonical to themselves. `/ru/products` was `noindex` and canonical to `/ru/catalog`. Draft, archived, deleted, missing, unpublished category, and `/xx` returned HTTP 404. The sitemap had 51 unique URLs on `http://catalog.example`, with xhtml alternates, and without drafts, search, admin, or API URLs. `robots.txt` allowed the three locales, disallowed admin, API, and the private media prefixes, and pointed at the sitemap.
- The same server with `PUBLIC_SITE_URL=http://localhost` kept the title and Organization name, omitted canonical, hreflang metadata, localhost hosts, SearchAction, the Sitemap line, and sitemap URLs.

### Current Alembic head (October 2026)

The latest Alembic revision is **`approved_uz_en_product_names`** (`api/alembic/versions/approved_uz_en_product_names.py`). It revises **`phase3_admin_sessions`**. It is a data migration that sets approved Uzbek and English `localized_name` values for **17** products (**34** locale rows). Matching is by stable product slug; divergent non-null admin names are not overwritten. Seven products remain unresolved and are intentionally omitted: **25, 469, 512, 515, 621, 636, 637**. Wording and deferrals are recorded in `docs/translation-approval-list.md`; the apply/revert helpers live in `api/app/data/approved_uz_en_product_names.py`.

Phase 7 itself added no Alembic revision. The historical Phase 7 statements below (and earlier in this section) remain accurate for that commit.

## Known limitations

- `product_translations.search_vector` exists and is not filled by a trigger or by application code.
- `business_profile.id` is fixed at 1.
- Image rows and import assets accept only `image/png`, `image/jpeg`, and `image/webp`.
- The audit log is append-only by application convention. The database does not block `UPDATE` or `DELETE`.
- If a Phase 2A database has source rows pointing at job ids and has no administrator, the new job foreign keys are `NOT VALID` until an operator validates them.
- Import upload, preview, resolution, and apply exist, and the admin screen uses those routes. A job is not given a separate approved status before apply.
- Database transactions do not include the filesystem. A failed stage leaves checksum objects in place so a shared hash is not deleted. Unreferenced checksums need a later cleanup that checks `product_images` and `import_assets`. Apply does not delete them.
- Apply does not leave a job in `applying`. The startup check described for a stuck `applying` job is not used by this path.
- Hikvision rows whose model and description do not name a verified brand are staged with a null brand. The worksheet name is not used as a brand. The local Hikvision workbook produced 530 `brand_unverified` rows under that rule.
- Hilook image anchors whose top-left cell is a heading stay `unassigned`. That pass found 20 such anchors. The analysis note of 7 non-product Hilook images is not treated as a reason to attach those images to the next product.
- `slug_redirects` is not created. Slugs are assigned once and the admin API does not change them, so there is no old URL to redirect. An unknown slug returns 404.
- `PUBLIC_SITE_URL` is still `http://localhost`. Canonical, hreflang, sitemap hosts, and absolute social URLs stay omitted until the client supplies the real origin. This is not a Search Console submission.
- Admin pages load their data in the browser after the server layout. They are not fully server-rendered forms.
- The language switch submits a navigation, so unsaved form text is lost.
- There are no per-field editor or edited-at columns. Locks and the audit log are the record of a manual change.
- Products are archived. Brands and categories have no delete route.
- Login limits live in one process. Multiple Uvicorn workers do not share them.
- Production session cookies are `Secure`. The current Nginx listener is HTTP until the client supplies a domain, so browsers will not store those cookies until TLS is added.
- The CSRF cookie is readable by script on this origin so the admin UI can send the header. The session cookie stays `HttpOnly`.
- Next.js development does not serve `/media/objects/`. Production Nginx does, and only that prefix. Workbooks under `imports/` and `private-uploads/` are not in the Nginx location.
- Deleting a product image removes the database row and does not delete the checksum file. A later cleanup still has to check other references.
- A repeated apply of an already `applied` job returns the stored result instead of rejecting the request. The admin screen hides Apply once the status is no longer `preview`.
- The Compose host-port failure on 5433 was observed on this Windows machine. It is not evidence that the same port fails on the Ahost VPS.

## Git

Remote `origin`: `https://github.com/ajiniyaz-dev/camera-shop`

Branch `main` tracks `origin/main`.

Phase 3 checkpoint: `c51f935ef0f051e7f98a5560f9803dedfc7aae5a`.

Phase 4 commit: `376b87185a594cbb1f77bdbdf83b0c18e4f7eb5c` — `Implement Excel import workflow`

That commit is on `origin/main`. It contains 21 files. The Phase 2A, Phase 2B, and Phase 3 migration files were not changed. The Excel workbooks were not modified and are not part of the commit. SHA-256: Hikvision `8B3CDE12879215CD2E28CCB9ABFACF61F305BA9320B400FF50ACB5403463FCAC`, EZVIZ `C4C3D2D4A3A36FB591C58B26FC21274E27E13D2150CEDEEAC0161C4D9566CDA5`.

Phase 1 and Phase 2A commit: `dfe902cd7d9fa65b7c8092b2efd82ae53a645a88` — `Complete project foundation and core database schema`

Handoff commit for that checkpoint: `2473d4b6a5d9f232add8cd69d1b23e660f15f13e`

Phase 2B commit: `af850e122c00c2f8a747ea78088daa0ce4dd08dd` — `Add import infrastructure schema`

Handoff commit for that checkpoint: `8703918509ebb9b1d62a10582c8faaec16496fbe`

Phase 3 commit: `1a1e294ded5ea3fda4e4de3212cec18e1dac73f1` — `Add secure admin authentication and sessions`

That commit is on `origin/main`. It contains 25 files. The Phase 2A and Phase 2B migration files were not changed. The Excel workbooks were not modified and are not part of the commit. SHA-256: Hikvision `8B3CDE12879215CD2E28CCB9ABFACF61F305BA9320B400FF50ACB5403463FCAC`, EZVIZ `C4C3D2D4A3A36FB591C58B26FC21274E27E13D2150CEDEEAC0161C4D9566CDA5`. This handoff note was added after that push.

Phase 5 commit: `a8614a03470995633ce5d8cc0dc84923782b9481` — `Complete admin panel and catalog management`

Phase 5 checkpoint: `8c056246f01f7beddd112ea6e3fce627cf1fb233` — `Record the published Phase 5 checkpoint`

That checkpoint is on `origin/main`. It contains the admin panel. No Alembic revision was added. The Excel workbooks were not modified.

Phase 5 hardening commit: `a8ff03579d14584197d3e330053752e141ae40a2` — `Harden admin workflows and verification`

That commit is the parent of the Phase 5 handoff note `3f1a55bacab65bbefb089e3aee41756caf72ef3f`. It changes the import review screen and this handoff. No Alembic revision was added. The Excel workbooks were not modified.

Phase 6 commit: `5c6b87a26c22d1ae25391c3cbcd1ecf6223ede4b` — `Implement public multilingual product catalog`

That commit adds the public catalog API, the `/ru`, `/uz`, and `/en` pages, and the public catalog tests. No Alembic revision was added. The Excel workbooks were not modified.

Phase 6 checkpoint: `7ff4db4fa517348c68e28c58368ae6c302896abc` — `Record the published Phase 6 checkpoint`

Phase 7 commit: `6b664ee64dd6f74d1196c4ebae38e0ffeef5194e` — `Implement technical SEO for public catalog`

That commit adds public metadata, canonical and hreflang handling, `/sitemap.xml`, `/robots.txt`, Open Graph, and JSON-LD. No Alembic revision was added. The Excel workbooks were not modified.

## Local catalog checkpoint — 16 October 2026

Verified against the running Compose database. No catalog rows were changed for this checkpoint.

- Products: 630 published, 10 draft, 1 archived. No product has `deleted_at` set.
- Import jobs 1–4 are `preview`. Job 5 is `applied`.
- Brand `other` (id 8) is unpublished. Category 38, slug `drugie-ustroystva`, name `другие устройства`, is unpublished.
- The public site for this machine is `http://127.0.0.1:8080`. Compose services `postgres`, `api`, `web`, and `nginx` are the local stack. Postgres is published on host port 5433 so it does not collide with a host PostgreSQL on 5432. The API container still uses `postgres:5432` on the Compose network.
- Products are archived, not deleted. The test rows are still present: product 1 `TEST-DO-NOT-SELL-001` is archived, and product 2 `ddmlwefwe` is a draft. There is no admin delete route.
- The other drafts are 13–17 (Seagate drives with empty Russian descriptions; 14 still has a desktop-drive photo the source does not name), 268 (Russian 25× optical zoom, English and Uzbek still say 15×, and the photo is shared with the published 15× model), 494 (`GDR-126035B` in the model and `GDR-126035BM` in the description), 528 (`гибкий переход`, still in unpublished category 38), and 533 (`2V 15A` in the model and 12V in the description).
- A custom-format `pg_dump` of this database is stored outside the repository, next to a short restore note. Dumps, `.env`, PostgreSQL data, and `data/source/*.xlsx` are not committed.

## Local catalog checkpoint — 17 October 2026

The two test products were removed through the admin delete route. Immediately after that deletion, product 528 was still a draft and its category assignment was locked. No other product had been published or deleted yet. The approved publications later on 17 October are the bullets below. The Excel workbooks were not modified.

- Products after the 17 October corrections: 639 published, 0 drafts, 0 archived. Products 13–17 and 528 were published with the approved descriptions. Category 38 `drugie-ustroystva` is published and contains only product 528.
- The removed rows are product 1 `TEST-DO-NOT-SELL-001` and product 2 `ddmlwefwe`. Their earlier audit rows remain. New audit actions `product_deleted` are ids 1619 and 1620.
- No drafts remain. Products 13–17 and 528 were published with the approved descriptions. Source cells are in `docs/unresolved-drafts.md`.
- Product 528 `гибкий переход` is published. Category 38 `drugie-ustroystva` is published and contains only that product. The public price remains 1.50 USD. This replaces the earlier statement that the product was still a draft and the category was still unpublished. The 16 October checkpoint above remains the record of that earlier state. `docs/unresolved-drafts.md` and the catalog accuracy audit agree with this published state.
- The running Compose API process was not rebuilt, so it does not yet serve the new delete route. The route is in the application code and was executed against this database from that code.

## Public presentation — 18 October 2026

The public pages now explain the catalog, label brand and category links, show the four video-history plans as services, and keep a browser-local selection. Details and the checks are in `docs/phase-2-completion-report.md`.

- A selection is a list stored in the browser. It is not a cart, an order, or a payment. There is no send or share action.
- Model codes are shown without a “Russian original” note. A Russian sentence used as a title still carries a short “In Russian” / “Rus tilida” / “На русском языке” label.
- Seagate has five published products, so it stays in the public brand list. A published brand with no published products is omitted from discovery. Brand records are not deleted.
- On 18 October the local Compose `web` and `api` images were rebuilt and those two containers were recreated. Postgres and nginx were not recreated. `camera-shop_postgres_data` and `camera-shop_catalog_media` stayed mounted. `http://127.0.0.1:8080` serves the new frontend and API. The earlier checks on port 3012 were against the dev server. The preview on port 3010 was not rebuilt and still returns 404 for `/ru/selection`.
- After the rebuild, port 8080 served the three selection pages, add/view/remove for BNC, the BNC photo at 105×60, the CS-H1C photo scaled down from 3508×2480, product 56’s no-image placeholder in Russian, Uzbek, and English, and the monthly and yearly service plans. Published products remained 639. `GET /api/health` returned ok.
- The final regression on port 8080 also confirmed the `IPC-B469HAD-LUF/SL` gallery switches images, and selection add, duplicate display, navigation, refresh, remove, and the empty state in Russian, Uzbek, and English. Typecheck passed. Frontend tests: 22 passed. Public catalog API tests: 7 passed on a disposable database that was removed. The core Phase 2 implementation and this local Docker verification are complete. Details are in `docs/phase-2-completion-report.md`.

## Authentication verification — 18 October 2026

Phase 3 authentication was already implemented. A logout response bug was corrected in source, and the local `api` image was then rebuilt. Only `camera-shop-api-1` was recreated. Postgres, nginx, and web were left running. `camera-shop_postgres_data` and `camera-shop_catalog_media` stayed mounted. No migration ran. The administrator account, catalog, import history, and audit log were not changed. Credentials were not reset.

Checked on `http://127.0.0.1:8080` after that rebuild:

- `GET /api/health` returned ok. Published products remain 639. One active administrator remains.
- Anonymous `GET /api/auth/me` and `GET /api/admin/dashboard` return 401.
- `POST /api/auth/logout` with no session cookie returns 204. That response deletes `hikvision_session` (`HttpOnly`, `Max-Age=0`, path `/api`) and `hikvision_csrf` (`Max-Age=0`, path `/`). The existing unexpired database session was not revoked by that anonymous request.

Not checked on the running site, because no browser held the administrator session and the raw token is not stored:

- Logout of that existing authorized session, including revocation and the browser being refused afterward.
- A following login with the existing administrator account. The password was not read or reset.

`tests/test_auth.py`: 18 passed again on a disposable Postgres container that was not attached to the Compose network. That container was removed. Those tests cover login, invalid credentials, logout with cookie deletion, unauthorized access, expiry, and CSRF. The Compose catalog was not used.

Phase 3 is not marked complete until the authorized logout and a following login are observed on port 8080.

## Preview failures — 18 October 2026

The three reported pages fail on port 3010 and work on port 8080. This is not an API or catalog defect.

Port 3010 is `npm run start` in `web/`, started with `API_INTERNAL_URL=http://127.0.0.1:8080`. Port 3012 is `next dev` in the same directory, so both use `.next`. The dev server replaced the production build. The preview still returns its old HTML, including `/uz/catalog`, `/uz/categories`, and `/admin/profile`. The hashed files that HTML requests, such as `/_next/static/chunks/webpack-a1f00b374570b680.js` and `/_next/static/css/efa22ffa85a43708.css`, return `400` with an empty Next error page. The browser then shows “Application error: a client-side exception has occurred”. The public API itself returns 200 for the product and category lists. The Uzbek error-boundary text `So'rov bajarilmadi` is not what these responses render.

On `http://127.0.0.1:8080` the same routes load. `/uz/catalog` lists products, `/uz/categories` lists categories, and `/admin/profile` redirects to `/admin/login` without a client exception. Static assets on that site return 200. No service was rebuilt for this check.

Do not run `next dev` and `next start` against one `.next` directory. Restoring the preview requires a production build while the dev server is not writing that directory, then a restart of port 3010 only.

## Phase 4 audit — 18 October 2026

The Excel import workflow was already implemented. The audit is recorded in `docs/phase-4-completion-report.md`.

Two defects were fixed in source, without a migration and without applying a workbook to the live catalog:

- Duplicate match keys in one file no longer make the existing product `absent_from_latest`.
- A field override on an excluded row returns 409 and no longer restores that row.

Isolated import tests: 50 passed before the rebuild, and the same 50 passed again afterward on a new disposable database (31 API and staging, 19 parser and schema). Frontend typecheck passed. Frontend library tests: 27 passed.

The local `api` and `web` images were then rebuilt with `docker compose --env-file .env -f docker-compose.yml -f docker-compose.dev.yml up -d --no-deps --build api web`. Postgres container `747524f4819c` and nginx container `d2b45c32481e` were not recreated. The named data and media volumes were kept. Port 8080 health stayed ok and the public catalog stayed at 639 products. Anonymous import reads and writes returned 401. `/admin/imports` redirected to `/admin/login`. The new images contain the duplicate-match and excluded-row fixes, and the upload page still has separate Hikvision and EZVIZ inputs. No workbook was uploaded or applied. No administrator session was available, so the signed-in preview screen was not used.

## Phase 5 audit — 18 October 2026

The admin panel was already implemented. The audit is in `docs/phase-5-completion-report.md`. Two defects were fixed in source: the product editor can no longer save before the product loads, and an unchanged specification list is no longer deleted and recreated. Product and brand lists no longer show an empty state during the first load.

The local `api` and `web` images were rebuilt with `docker compose --env-file .env -f docker-compose.yml -f docker-compose.dev.yml up -d --no-deps --build api web`. New containers: api `991c9d0c1b1b`, web `2f4463ac00e1`. Postgres `747524f4819c` and nginx `d2b45c32481e` were not recreated. Both named volumes stayed mounted.

Nginx was still using the previous edge addresses, which the new containers had swapped, so port 8080 returned 502. `nginx -s reload` inside the existing nginx container resolved the new addresses. Nginx’s start time stayed 06:34 UTC. After that reload, health was ok, `/uz/categories` returned 200, and the public catalog stayed at 639 products.

The API image contains the unchanged-specification comparison. The web image disables save until `canSaveLoadedProduct` allows it, and disables archive and delete until the product has loaded. Anonymous `/api/auth/me` and `/api/admin/products` returned 401. Anonymous logout returned 204 and left the three unexpired administrator sessions in place. The browser opened `/admin/products` and landed on `/admin/login`. No administrator session was available, so the product list, editor, unchanged save, and authorized logout were not used. Credentials were not read or reset. Phase 5 is not complete.

`tests/test_catalog_admin.py`: 9 passed in 16.44s on disposable Postgres `cs-pytest-pg`, which was removed afterward. Frontend typecheck passed. Frontend library tests: 29 passed.

## Phase 6 verification — 18 October 2026

Requirements are in `docs/project-requirements.md`. Details and Docker evidence are in `docs/phase-6-completion-report.md`. Production blockers and the deploy runbook are in `docs/production-readiness-report.md`. No schema migration. No catalog row, import, or workbook was changed.

`api/app/pricing.py` converts stored USD with Decimal: Hikvision × 9600, EZVIZ × 10800, half-up to a whole soʻm. `source_code` selects the formula. Missing provenance returns `unavailable`. The public router returns UZS, filters and sorts on displayed soʻm, and leaves stored USD untouched. The selection page sums numeric UZS rows and discloses excluded on-request and unavailable rows. Structured data uses `UZS`. There is no checkout.

The local `api` and `web` images were rebuilt with `docker compose --env-file .env -f docker-compose.yml -f docker-compose.dev.yml up -d --no-deps --build api web`. New containers: api `3814f83ef46a`, web `546fb3d6c098`. Postgres `747524f4819c` and nginx `d2b45c32481e` were not recreated. Both named volumes stayed mounted. Nginx was reloaded so upstream addresses refreshed.

Checked on `http://127.0.0.1:8080` after that rebuild:

- `GET /api/health` returned ok. Published products remain 639 (555 hikvision, 84 ezviz provenance).
- `product-12v-10a`: stored 4.00 USD → 38 400 UZS. HiLook `hilook-ipc-b469had-luf-sl`: stored 115.00 USD → 1 104 000 UZS. EZVIZ `ezviz-cs-c60p-3mp`: stored 50.00 USD → 540 000 UZS.
- Soʻm price filters work. Product cards and detail pages show soʻm. Selection totals 1 158 000 сум for HiLook + EZVIZ monthly; adding WD on-request keeps that total and shows the exclusion disclosure. `/ru/checkout` and `/ru/cart` return 404.

Isolated tests after the rebuild: `tests/test_pricing.py` plus `tests/test_public_catalog.py` — 13 passed on disposable Postgres that was removed. Frontend typecheck passed. Frontend library tests: 32 passed.

Phase 6 is complete for the local Docker site.

After that verification, the header selection control was changed from a text link to a red Lucide shopping-cart icon with a live count badge. It still opens `/{locale}/selection` only (`SelectionLink` shared in the site header for desktop and mobile).

The first icon pass left an outdated `web` image on port 8080 (still showing text `Подборка`). On 18 October the `web` image was rebuilt and the container recreated (`29fce25c3083`); postgres, api, nginx, and volumes were preserved; nginx was reloaded. Port 8080 then served the red Lucide cart with live badge counts and localized `aria-label` values. Frontend selection tests: 6 passed. Typecheck passed.

A later UI pass shared Lucide outline icons across product cards (selection cart accent `#FF414D`, muted model/brand/category/price marks), homepage category tiles, and subcategory links. Mapping uses the existing reliable `categoryMark` slug rules; ambiguous sections stay neutral. Selection and pricing behavior were unchanged. The `web` image was rebuilt again for that pass.

Category directory bug (uneven stretched cards and nested series lists on `/uz/categories`) was a layout issue, not bad catalog data: a two-column CSS grid stretched short parents beside tall ones that recursively nested children. `CategoryIndex` now uses a compact three-column card grid with chip-style child links. Customer-facing “selection” labels were renamed to cart terminology (EN/RU/UZ); canonical URL is `/{locale}/cart`, with `/{locale}/selection` redirecting there. Persisted cart storage keys are unchanged.

## Next task

Phase 8 — production deployment and hardening — is blocked on client and ops inputs recorded in `docs/production-readiness-report.md` and `docs/open-questions.md`. Supply the real HTTPS origin, then set `PUBLIC_SITE_URL` and `MEDIA_PUBLIC_BASE_URL`, add TLS/HSTS to nginx, use a non-placeholder `SESSION_SECRET`, schedule database and media backups, and restore once on the VPS before any public cutover. Do not invent a domain, phone, email, address, or social URL. Do not modify `data/source/`. Do not add checkout, payments, customer accounts, or orders. Do not expose the site beyond loopback until those inputs exist.

Phase 5 is still open for signed-in checks. Sign in once with the existing administrator account on `http://127.0.0.1:8080/admin/login` when that check is wanted. Confirm the product editor loads before it can be saved, then log out and confirm `/api/auth/me` returns 401. Do not reset the password. Phase 3 authorized logout/login on port 8080 remains open for the same reason.

Still deferred from Phase 2: a genuine photo for product 56, the rejected workbook drawings, and an optional send or share action for the selection.
