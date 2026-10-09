# Architecture

Modular monolith for the HikVision public catalog and a private admin. One Next.js frontend, one FastAPI backend, one PostgreSQL database, and a media directory. Nginx terminates HTTPS and routes traffic.

The site owner is HikVision. Product brands are data, not a second application.

No Redis, Celery, Kafka, or Kubernetes. Import state, sessions, and audit rows live in PostgreSQL. The import runs in the API process.

## Components

### Frontend

- Next.js, TypeScript, Tailwind CSS.
- Public pages use server rendering, and static generation or incremental regeneration where the content is published catalog data. The HTML response includes the H1, price state, and available description.
- Locales are path prefixes: `/ru`, `/uz`, and `/en`. A language switcher points at the same page in the other locales.
- Interface strings (navigation, buttons, forms, validation, errors, price status, stock status) live in message catalogs for `ru`, `uz`, and `en`, not in the database.
- Product, category, and brand copy live in translation rows. The Russian source text is the `ru` content.
- Admin is under `/admin`. It uses the same three message catalogs. It is not linked from the public site and is `noindex`.
- The browser calls `/api/...` on the same host so the session cookie stays first-party.

### Backend

FastAPI, Pydantic, SQLAlchemy. Modules:

| Module | Responsibility |
| --- | --- |
| `catalog` | Brands, categories, products, translations, stock, public read models |
| `media` | Checksums, object keys, public URLs, upload checks |
| `imports` | Identify the workbook, validate, stage, preview, apply one job |
| `identity` | Admin users, sessions, authorization |
| `seo` | Slugs, redirects, sitemap, hreflang data |
| `settings` | Company profile, contact details, social links |
| `audit` | Append-only log of sensitive admin actions |

Public and admin Pydantic models are different types. A public route must not return the admin model.

### Database

PostgreSQL holds the live catalog, translations, sessions, import jobs, source mappings, and audit log. It does not hold image binaries or workbook binaries.

### Media

Initial storage on the Ahost VPS:

- Docker volume mounted at `/var/lib/catalog/media`.
- Content-addressed public objects: `media/objects/{sha256[0:2]}/{sha256}.{ext}`.
- Import originals, not public: `media/imports/{job_id}/{source_code}.xlsx`.
- The database stores `object_key`, checksum, MIME type, and byte size.
- Nginx serves `/media/` from the public prefix only. Directory listing is off.
- `storage_backend` is `local`. A later value `s3` keeps the same key and changes the URL builder. Public URLs come from `MEDIA_PUBLIC_BASE_URL`.

The files in `data/source/` are never modified. Uploads are copies.

### Admin

Server-rendered screens for the capabilities in `docs/project-requirements.md`. There is no separate admin application. Import preview and apply are part of this UI.

## Public request flow

1. A request arrives at `/{locale}/...`. Unknown locale prefixes return 404. `/` redirects to `/ru/...` (Russian is the source language and the default).
2. Next.js loads the public API for that locale.
3. FastAPI returns only published, non-archived rows and only public fields.
4. Localized product copy comes from the requested locale. If that translation is missing, the API returns the Russian original and `translation_fallback: true`. The page shows it as the original Russian text, using a UI label that is itself translated. It does not label the Russian paragraph as Uzbek or English.
5. Price rendering:
   - `numeric` — the decimal amount with a `$` prefix. No discount and no second price.
   - `on_request` — the locale’s request-price string: Russian `По запросу`, Uzbek `So'rov asosida`, English `On request`.
6. Stock rendering: the payload may include `out_of_stock`. The page draws a badge only in that case, with `Нет в наличии`, `Mavjud emas`, or `Out of stock`. In stock adds no badge and no quantity.
7. The page emits canonical and `hreflang` links for `ru`, `uz`, and `en`.

Search, brand, and category pages use the same public schema. Filters use an allow-list, not raw column names.

## Admin request flow

1. `/admin` requires a session.
2. Every `/api/admin` handler checks the session and that the user is an active administrator.
3. Writes are validated, then committed, then recorded in the audit log when the action is sensitive (login, price change, publish or archive, contact change, import apply).
4. Editing a protected field sets that field’s lock and stores the editor and time. A later import will not replace the locked value unless this job’s preview resolution says to accept the Excel value.
5. Company name defaults to `HikVision`. Phone, email, address, hours, domain, and social links stay empty until an administrator saves real values. The public contact page renders only filled fields.

## Authentication flow

1. Login accepts email and password over HTTPS.
2. The API verifies an Argon2id hash. The password is not stored or logged.
3. A session row stores a hash of a random token. The cookie is `HttpOnly`, `Secure`, and `SameSite=Lax`.
4. Logout revokes the session and clears the cookie.
5. State-changing admin requests also require a CSRF token.
6. There is no public registration and no customer account.

## Excel import flow

One admin area handles both sources. A job contains one or two files. Uploading and previewing do not write live catalog rows.

1. The administrator uploads `Hikvision pr.xlsx`, `Ezviz pr.xlsx`, or both.
2. Each file is identified from its headers and sheet structure. The filename is supporting evidence only. Ambiguous identity stops that file and asks for confirmation or returns a validation error. Data is never written into the other source.
3. Each valid file is parsed, compared only with that source’s last applied mappings, and staged.
4. The other source is not read and not marked absent.
5. The preview lists both files when both were uploaded, and it shows which source is absent from this job.
6. The administrator excludes bad rows, confirms uncertain matches, and chooses keep-or-accept for conflicts with manual edits. Defaults do not overwrite locked fields. `Replace prices with Excel values` is off unless explicitly enabled, and the preview lists every manual price it would replace.
7. **Apply approved changes** runs once for the whole job. It updates only the sources included in the job.
8. If one file is invalid, the valid file can still be previewed and applied on its own. The invalid file contributes nothing. The live catalog stays unchanged until an apply succeeds.
9. A second apply of the same job is rejected.
10. Products that were not in the uploaded file stay in the catalog and are reported as absent from that source. They are not archived automatically.

Details are in `docs/import-strategy.md`.

## Deployment

One Compose stack on the Ahost VPS:

| Container | Role |
| --- | --- |
| `nginx` | HTTPS, headers, `/` to Next.js, `/api/` to FastAPI, `/media/` from the public media prefix |
| `web` | Next.js |
| `api` | FastAPI, including the importer |
| `postgres` | PostgreSQL, not published on the host’s public interface |

- Restart policy: `unless-stopped`.
- Secrets come from the server environment, not the image.
- Database files and the media volume are separate volumes.
- Schema changes are migration files applied before the API serves traffic. Migrations are forward-only in production.
- Health check: `GET /api/health` checks the process and a trivial database query.
- Rollback of a bad release is redeploying the previous application image. A migration that has already been applied is not guessed backward. Restore the database backup if the migration itself must be undone.
- Production runs with debug mode off and interactive API docs disabled.

## Request boundaries

- Public routes read the public schema only.
- Admin routes are the only readers of discount notes, source headers, import diagnostics, lock flags, and audit detail.
- The importer is the only writer of source-snapshot columns, and only for the source codes in the job being applied.
- Manual product edit is the only writer that sets lock flags.
- Image bytes are written by the importer and by admin upload. Both use the same content, type, and size checks.
