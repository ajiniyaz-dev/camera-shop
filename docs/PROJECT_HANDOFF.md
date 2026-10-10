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

- Numeric prices are USD, stored as decimals, shown with `$`. No conversion.
- Show only the main price. Do not calculate or display discounts.
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
- `import_rows` — staged worksheet rows. Classification, action, resolution, raw cells, proposal, messages, matched product, and applied flag. Unique `(import_file_id, worksheet_name, source_row)`. Pending `conflict` and `possible_match` rows cannot be marked applied. `accept_excel` is the explicit approval to overwrite a manual value. `replace_prices` on the job defaults to false.
- `import_assets` — extracted images, including `unassigned` and `shared_candidate`.
- `admin_audit_log` — `actor_id` is nullable so an unknown failed login can be recorded. Detail JSON cannot contain `password`, `password_hash`, `secret`, `session_token`, or `token` keys.

`publish_new_products` is `BOOLEAN NOT NULL DEFAULT TRUE` on `import_jobs`. Documented job statuses are `preview`, `rejected`, `applying`, `applied`, and `failed`. Those cover upload (the job and file rows), validation (`import_files.validation_status`), review (`preview` plus row resolution), applying, completed (`applied`), and failed. `applied` requires `applied_at`. `preview` and `rejected` cannot have `approved_by`.

`product_source_records.first_job_id` and `last_job_id` now reference `import_jobs` with `ON DELETE RESTRICT`. On upgrade, existing catalog rows are kept. Referenced job ids are backfilled as `applied` jobs when an administrator already exists. If source rows point at missing job ids and no administrator exists, the foreign keys are added `NOT VALID` and those source rows stay. Downgrade to `phase2a_core` drops the import tables and leaves the Phase 2A rows.

Not created in Phase 2B: `admin_sessions`, `slug_redirects`. No workbook parser, image extractor, import endpoint, CRUD API, authentication endpoint, admin UI, public page, or SEO output.

### Phase 3

Verified by `api/app/auth/`, `api/app/cli/create_admin.py`, and Alembic revision `phase3_admin_sessions` in `api/alembic/versions/phase3_admin_sessions.py`. It revises `phase2b_import`. The Phase 2A and Phase 2B migration files were not rewritten.

- `POST /api/auth/login` checks Argon2id, writes a generic failure, and on success sets cookies and returns `id`, `email`, `role`, and `csrf_token`.
- `POST /api/auth/logout` revokes the session when the CSRF token and origin match, then clears the cookies. A missing session still clears cookies and returns 204.
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
- `PATCH /api/admin/imports/{job_id}/rows/{row_id}` sets `keep_current`, `accept_excel`, `accept_new`, or `exclude` on a row that belongs to that job.
- `POST /api/admin/imports/{job_id}/assets/{asset_id}/exclusion` records an asset id in the job summary. There is no excluded column on `import_assets`.
- `POST /api/admin/imports/{job_id}/apply` with `{"confirm": true}` applies the job once.
- `POST /api/admin/imports/{job_id}/reject` sets `rejected` from `preview` only.

`preview` can become `applied`, `rejected`, or `failed`. A repeated apply of an `applied` job returns the stored result. A 409 for unresolved rows leaves the job in `preview`. An unexpected apply error rolls the catalog transaction back and then marks the job `failed`. This path does not persist `applying`, so there is no stuck-`applying` recovery step.

A possible match stays `pending` and blocks apply. Its field differences and lock defaults are stored on the row. `accept_excel` is the explicit decision that overwrites locked fields on that row. A conflict cannot choose one Excel value. A row from another job is rejected. A missing workbook does not delete or flag the other source.

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

`GET /api/admin/imports` lists recent jobs. Import row responses now include `current` when the row is matched to a product: display model, option, Russian brand and category names, Russian description, public price, and lock flags. Asset responses include `anchor_model` when a staged row shares the file, worksheet, and anchor row. The review screen shows the worksheet, classification, action, resolution, message codes, exclusion, and the incoming price, brand, category, and description. When `field_changes` is present it shows the current value, the incoming value, and the field resolution. A locked public price is called out with both amounts. Choosing `accept_excel` asks for confirmation and names the fields that are still `keep_current`. Conflicts can be kept or excluded; they cannot take `accept_excel`. Apply is offered only while the job is `preview`, and only after the confirmation checkbox. A failed apply, including HTTP 409, leaves the status unchanged. `replace_prices` stays an upload option and does not bypass the row rules.

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
- `slug_redirects` is not created. The public catalog and SEO output are not built. Admin catalog routes exist; there is no public product API.
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

Phase 5 hardening follows that checkpoint. The commit hash is recorded in the note added immediately after the hardening commit.

## Next task

Phase 6 — Public Multilingual Product Catalog. Do not modify `data/source/`.
