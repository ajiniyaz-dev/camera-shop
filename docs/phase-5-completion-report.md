# Phase 5 — Admin panel and catalog management

18 October 2026. The admin panel was already implemented. This pass audited it, fixed two confirmed defects, and did not change the live catalog.

## Already in place

The panel is at `/admin` and is not linked from the public site. Reads use `require_admin`. Writes use `require_admin_write`, which checks the session, the administrator role, and CSRF. The browser does not store the session in `localStorage` or `sessionStorage`.

Already covered by the catalog API and admin screens:

- Product list with search, brand and category filters, status, stock, sort, and pagination.
- Create and edit products, including Russian, Uzbek, and English names and descriptions.
- Numeric, on-request, and hidden prices. An on-request price cannot carry an amount. A numeric price needs a non-negative amount with at most two decimal places. A manual price change sets `price_locked`.
- Stock is separate from price. Out-of-stock is an explicit status.
- Publish, draft, and archive. Archive asks for confirmation. Unpublished and archived products stay out of the public catalog query.
- Specifications in Russian, with optional Uzbek and English.
- Image upload, primary selection, and removal of the association. Removing an image row does not delete the stored file.
- Brand and category names and translations. Slugs are assigned on create and are not rewritten when the name changes. A category cannot be its own parent or form a cycle. A parent move that would duplicate a sibling slug returns 409.
- Sensitive actions append `admin_audit_log`. There is no public audit page. The log is not part of a public response.
- A confirmed permanent delete exists in the worktree. It requires the typed model text, keeps shared image files and import rows, and is separate from archive. It was not used on the live catalog.

## Defects fixed

1. The product editor could submit a save, archive, or delete before the existing product finished loading. An early save would send empty fields. Save, archive, and delete now stay disabled until that record has loaded, and a failed load shows the error instead of an empty form.
2. Every product save sent the current specifications, and the API deleted and recreated them even when the text was unchanged. An identical specification list now stays on the same rows and is not recorded as a specification change. A real text change still replaces the rows.
3. The product list and brand list showed the empty state while the first request was still running. They now show a loading state, and a failed load is not presented as an empty catalog.

## Tests

Disposable Postgres `cs-pytest-pg` on `127.0.0.1:55432`, not the Compose catalog. The container was removed afterward.

| Command | Result |
| --- | --- |
| `pytest tests/test_catalog_admin.py` | 9 passed in 10.85s |
| `npm run typecheck` in `web/` | Passed |
| Frontend library tests | 29 passed |

The new API case creates a specification, saves the same text, and checks that the specification id is unchanged and the audit changes do not include `specifications`. A changed Russian value still replaces the row and keeps the English value. Existing cases still cover authentication, CSRF, prices, stock, search, archive, shared images, and draft slug correction.

The frontend tests cover the save guard and the list loading, error, and empty states.

## Docker checks before the rebuild

On port 8080, without an administrator session:

- `GET /api/health` returned ok, including the database.
- The public catalog total stayed 639.
- `GET /api/admin/products` returned 401.
- Opening `http://127.0.0.1:8080/admin/products` redirected to `/admin/login`.

## Rebuild — 18 October 2026

Only `api` and `web` were rebuilt:

`docker compose --env-file .env -f docker-compose.yml -f docker-compose.dev.yml up -d --no-deps --build api web`

| Service | Container | Result |
| --- | --- | --- |
| api | `991c9d0c1b1b` | Recreated, healthy |
| web | `2f4463ac00e1` | Recreated, healthy |
| postgres | `747524f4819c` | Left running, started 06:34 UTC |
| nginx | `d2b45c32481e` | Left running, started 06:34 UTC |

`camera-shop_postgres_data` and `camera-shop_catalog_media` stayed in place. The API container still mounts the media volume at `/var/lib/catalog/media`.

Nginx resolves `api` and `web` when its configuration loads. The recreated containers received the previous edge addresses in the opposite assignment, so port 8080 returned 502 until `nginx -s reload` ran inside the existing nginx container. That reload did not recreate nginx, and its start time stayed 06:34 UTC.

After the reload:

- `GET /api/health` returned `{"status":"ok","database":"ok"}`.
- `GET /api/public/products?locale=ru&page_size=1` returned total 639.
- `GET /uz/categories` returned 200.
- `GET /api/auth/me` and `GET /api/admin/products` returned 401.
- `POST /api/auth/logout` with no session cookie returned 204. The three unexpired administrator sessions stayed unrevoked.

The API image contains the specification comparison (`incoming == stored`). The web image contains the save guard `void 0===e||a` and the list state that returns loading while a count is still zero. The save button is disabled through that guard. Archive and delete are disabled while the loaded flag is false.

## Browser checks

`http://127.0.0.1:8080/admin/products` loaded the Uzbek login page: heading Kirish, Email, Parol, and the Kirish button. The browser held no administrator session. Credentials were not entered, printed, or reset.

These signed-in checks remain pending:

- Product list loading, empty, and error states.
- An existing product editor, including the loading line and disabled save, archive, and delete actions before the record arrives.
- A save that leaves specification ids and the other product fields unchanged.
- Logout of an authorized session, then a 401 from `GET /api/auth/me`.

A field-identical save still appends one `admin_audit_log` row. It does not replace specification rows when the submitted text matches the stored text. That save was not run on the live catalog.

## Catalog data

No live catalog row, image file, credential, volume, or source workbook was changed. Published products remain 639. One administrator account remains.

## Tests after the source fixes

Disposable Postgres `cs-pytest-pg` on `127.0.0.1:55432`, not the Compose catalog. The container was removed afterward.

| Command | Result |
| --- | --- |
| `pytest tests/test_catalog_admin.py` | 9 passed in 16.44s |
| `npm run typecheck` in `web/` | Passed |
| Frontend library tests | 29 passed |

The earlier run of the same catalog file, before this rebuild, was 9 passed in 10.85s on a disposable database that was also removed.

## Remaining risks

- Phase 5 is not complete. The signed-in product list, editor, unchanged-specification save, and logout have not been observed on port 8080.
- Permanent delete can remove a product and an image file that no other product, import asset, or logo uses. Archive remains the normal way to hide a product.
- Audit rows are stored and are not shown in the admin panel.
- Published product slugs stay put when the model changes. Only a draft model correction allocates a new slug.
- Phase 3 is still open until an existing administrator signs in and out on port 8080.
- Another recreate of `api` or `web` will need the same nginx reload, because the proxy names are resolved when nginx loads its configuration.

## Next step

Sign in once in the browser at `http://127.0.0.1:8080/admin/login` with the existing administrator account. Confirm the product list and one existing editor, save that product only if the form is unchanged, then log out and confirm `/api/auth/me` returns 401. Do not reset the password. Do not apply a workbook, archive a live product, or delete one.
