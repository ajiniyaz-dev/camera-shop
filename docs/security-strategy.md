# Security and operations

Baseline for one Ahost VPS. It covers authentication, the public/admin boundary, upload safety, backups, and import recovery. It does not add another datastore or a separate security product.

## Public and admin separation

- Public DTOs include only fields marked public in `docs/database-design.md`.
- Admin DTOs may include provenance, locks, import messages, and internal notes.
- Public routers do not read `internal_note`, `source_price_header`, `raw_cells`, password hashes, session hashes, or absolute paths.
- A numeric price is returned as a decimal amount and currency `USD`. The public page adds `$`. No discount field exists on the public schema.
- Request-price rows return status `on_request` and no amount, whether the source cell was explicit `По запросу` or blank. The source kind stays on the admin source record.
- A hidden price omits the amount.
- Discount notes on Hilook `F103`, `F106`, `F107`, and `F115` are internal.
- The EZVIZ header `Цена для дилера` is never a public field. The amount is public because it is the approved price.
- Unpublished and archived products are excluded by the query, not by the frontend.
- Every `/api/admin` route, including preview and read-only import detail, checks authentication and an active administrator.

## Authentication and sessions

- Administrators are rows in `admin_users`. There is no self-registration.
- Passwords use Argon2id. Plaintext and reversible encryption are not acceptable.
- Login is rate-limited in the API process, about 10 attempts per IP per 15 minutes. Upload is limited more loosely per administrator so a mistake cannot flood the disk. Redis is not required.
- The session cookie is `hikvision_session`: `HttpOnly`, `SameSite=Lax`, path `/api`. It is `Secure` when `APP_ENV=production`. Local HTTP development does not set `Secure`. The database stores an HMAC of the token, keyed by `SESSION_SECRET`, not the raw token.
- Sessions expire after `SESSION_TTL_SECONDS` (default 12 hours) and are revoked on logout. Each request checks `is_active`.
- State-changing admin requests require the CSRF token in both the non-`HttpOnly` cookie `hikvision_csrf` and the `X-CSRF-Token` header. The database stores only an HMAC of that token. A new login rotates it. Logout, expiry, and revocation discard it. The request `Origin` or `Referer` must match `PUBLIC_SITE_URL` or the request host.
- Login limiting is in-process: `LOGIN_RATE_LIMIT_MAX` failures per address per `LOGIN_RATE_LIMIT_WINDOW_SECONDS` (defaults 10 and 900). It is not shared across workers. `TRUST_PROXY=true` uses `X-Real-IP` only. Client `X-Forwarded-For` is ignored. Nginx replaces `X-Real-IP` with the connecting client. Set `TRUST_PROXY` only when that proxy is the only path to the API.
- Read routes use `require_admin`. State-changing admin routes use `require_admin_write`, which also checks the CSRF token and origin.
- CORS is unnecessary when Nginx serves the UI and the API on one host. If it is enabled, it allows only that origin.
- The first administrator is created by `python -m app.cli.create_admin [email]`. The password is prompted, not accepted on the command line, and not committed. The command refuses when an administrator already exists.

## Authorization and audit

- Launch role is `admin`, checked on the server for every admin operation.
- Sensitive actions append `admin_audit_log`: login success and failure, price change, publish, unpublish, archive, profile and social-link changes, and import apply. The detail JSON has no password, session token, or full workbook.
- Public routes cannot read the audit log.

## Validation and malicious workbooks

- Pydantic validates query and body fields: page size, slug pattern, sort allow-list, price bounds, locale allow-list, stock allow-list.
- SQL uses bound parameters. Search text is a parameter to the full-text function.
- Excel descriptions are stored and rendered as text, not as HTML.
- Upload names are discarded. Stored names are job ids, source codes, and checksums.
- Workbooks: administrator only, `.xlsx` only, 40 MB, ZIP signature and workbook part required. Macros are not executed. The file is not opened in Excel on the server. The copy is outside `/media/`.
- A workbook that fails identification or required headers is not applied. It cannot delete products.
- Images, extracted or uploaded: PNG, JPEG, or WebP by content sniff, maximum 15 MB, must decode as an image. Other types are rejected and reported.

## Secrets and transport

Server environment, not git:

- `DATABASE_URL`
- `SESSION_SECRET`
- `MEDIA_ROOT`
- `MEDIA_PUBLIC_BASE_URL`
- `PUBLIC_SITE_URL` (placeholder until the real domain is supplied)

No third-party API key is required for the catalog.

- PostgreSQL listens on the Docker network only. The application user is not a superuser.
- Nginx terminates HTTPS and redirects port 80. HSTS is enabled after the certificate is confirmed.
- Headers: `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-Frame-Options: DENY` or `frame-ancestors 'none'`, and a content security policy that allows the site’s own scripts and `/media` images.
- Production sets debug off and disables interactive API documentation.

## Logging and health

- Logs include a request id, status, and route. They omit passwords, session tokens, and full worksheet rows.
- Import failure logs the job id and exception type. Row detail stays in the admin report.
- Public errors are generic.
- `GET /api/health` checks the process and a trivial database query. It does not check import success; that is the job status.
- Disk space is checked before backups. The current drawings are about 34 MB; checksum storage will grow as staff add images.

## Backups and restore

- Daily `pg_dump`, retained at least 14 days, copied off the VPS when a second target exists.
- Daily copy of the media volume. A database backup without the image files is not a full catalog restore.
- `data/source/` stays the untouched client input. Import copies are not a substitute.
- Before launch, restore one dump and the media volume and open one product page.
- A failed backup job must be visible in logs.

## Migrations, deploy, rollback

- Schema changes are migration files applied before the new API serves traffic.
- Production migrations are forward-only. Rolling back a bad application build means deploying the previous image that still matches the applied schema.
- If a migration itself must be undone, restore the database backup taken immediately before it. Do not hand-edit production tables.
- Containers use `unless-stopped`.

## Import retry

- Preview writes no live catalog rows.
- Apply commits in one transaction. Failure rolls that transaction back and marks the job `failed`.
- A job in `applied` cannot be applied again.
- A job left in `applying` after a crash is marked `failed` on startup if the catalog transaction did not commit.
- Checksum files written before a rollback may be unreferenced. Cleanup deletes only keys that no table references.
- Retrying after failure means a new job, not a second commit of the failed one.
- Applying a Hikvision file does not write EZVIZ rows, so a retry cannot wipe the other source.

## Checks before launch

- Public JSON for a numeric EZVIZ price shows USD and no dealer column name.
- Public JSON for Hilook `E103` shows 115 and does not show the `F103` note.
- Public JSON for an explicit `По запросу` row and a blank HDD price both show `on_request` and no amount. Admin detail still shows source kind `blank` for the HDD row.
- An unauthenticated admin request returns 401.
- `/media/` does not list directories.
- Postgres is not reachable from the public internet.
- One backup restore has been done.
- Production debug mode is off.
