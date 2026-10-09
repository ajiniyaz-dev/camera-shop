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

These rules are specified and are not implemented yet. One admin import area. A job may contain the Hikvision file, the EZVIZ file, or both.

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

### Test result

On 2026-10-09, `pytest -q` of `tests/test_core_schema.py`, `tests/test_price_labels.py`, `tests/test_health.py`, and `tests/test_config.py` reported **22 passed** and 1 Starlette deprecation warning. That run included migration upgrade, downgrade, and upgrade again.

The schema tests did not use the Compose `catalog` database. Host connections to the Compose Postgres published port `127.0.0.1:5433` timed out, and port 5432 was already taken by another server. A disposable PostgreSQL 16 container was published on `127.0.0.1:55432`. The tests created and then dropped `catalog_phase2a_test` and `catalog_phase2a_roundtrip`. The disposable container was removed afterward.

Checked inside the Compose Postgres container at that time: database `catalog` had no tables. It was not migrated and was not dropped.

This handoff does not claim a newer full test run than that one.

## Known limitations

- `product_source_records.first_job_id` and `last_job_id` are required integers with no foreign key. `import_jobs` does not exist yet.
- `product_translations.search_vector` exists and is not filled by a trigger or by application code.
- `business_profile.id` is fixed at 1.
- Image rows accept only the three MIME types above.
- Import parsing, staging, preview, and apply are not implemented.
- These designed tables are not created yet: `import_jobs`, `import_files`, `import_rows`, `import_assets`, `admin_sessions`, `admin_audit_log`, `slug_redirects`.
- Login, CRUD APIs, admin UI, public catalog routes, and SEO output are not implemented.
- The Compose host-port failure on 5433 was observed on this Windows machine. It is not evidence that the same port fails on the Ahost VPS.

## Git

Intended remote: `https://github.com/ajiniyaz-dev/camera-shop`

At the time this section was first written, branch `main` had no commits and no remote. Excel workbooks, `.env`, virtual environments, `node_modules`, and build output are gitignored. The commit hash and push result are filled in after the checkpoint is published.

## Next task

Phase 2B, and only the import-related database infrastructure:

- `import_jobs`, `import_files`, `import_rows`, and `import_assets`
- foreign keys from `product_source_records.first_job_id` and `last_job_id` to `import_jobs`
- `publish_new_products` on `import_jobs`, default true

Do not implement Excel parsing, image extraction, admin UI, authentication, sessions, the audit log, slug redirects, or public catalog pages in that task. Do not modify `data/source/`.
