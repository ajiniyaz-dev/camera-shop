# Phase 6 — Public UZS pricing and product list

18 October 2026. Requirements are in `docs/project-requirements.md`. Source work and Docker verification on port 8080 are complete.

## What changed

### Shared pricing

`api/app/pricing.py` converts a stored USD amount with exact `Decimal` arithmetic:

| `source_code` | Formula | Example |
| --- | --- | --- |
| `hikvision` | × 12000 × 0.8 (= 9600) | 4.00 → 38,400 |
| `ezviz` | × 12000 × 0.9 (= 10800) | 50.00 → 540,000 |

Half-up rounding to a whole soʻm. The workbook code selects the formula, not the brand. HiLook products in the Hikvision workbook use the Hikvision factor. Missing or unknown provenance with a numeric stored price becomes `unavailable`. `on_request` and `hidden` stay without amounts. Stored `public_price_amount` and `public_currency` are not rewritten.

### Public API

`api/app/public/router.py` loads `product_source_record`, builds the public price through `public_display_price`, and filters or sorts on the displayed soʻm amount. Price bounds are whole soʻm values.

### Frontend

`web/src/lib/price-format.ts` formats API soʻm amounts and sums selection totals. It does not apply the workbook formula again. Product cards, detail pages, home search, home cards, and the selection page use that formatter. Structured data offers use `priceCurrency: "UZS"`. The selection page shows a combined total and a disclosure when on-request or unavailable rows are excluded. Browser persistence, deduplication, the 50-item cap, and 404 cleanup are unchanged. There is no checkout, cart, payment, or order step.

Header navigation uses a shared Lucide `ShoppingCart` icon (`#FF414D`) with a compact count badge (`SelectionLink` in `site-header.tsx`, desktop and mobile). It is the only public selection navigation control; the footer and main nav keep text links for home/catalog/categories/contact only. The control links to `/{locale}/selection`, keeps the existing `localStorage` selection and `SELECTION_EVENT` sync, and exposes a localized `aria-label` (for example `Подборка: 0`). Pure helpers `selectionNavHref`, `selectionNavLabel`, and `selectionBadgeCount` cover href, empty/filled labels, badge counts, and add/remove sync in `selection.test.mts`.

**Root cause of the reported broken icon:** source already had the red cart, but the Compose `web` image was not rebuilt, so port 8080 still served the old text link `Подборка` + count. After rebuilding only `web` (container `29fce25c3083`) and reloading nginx, HTML on 8080 shows `stroke="#FF414D"`, `lucide-shopping-cart`, and `aria-label` / `href` for `/ru|uz|en/selection`. Browser checks confirmed badge updates on remove (`3`→`2`), localized labels, and navigation to the selection page.

## Tests (isolated)

Disposable Postgres `cs-pytest-pg` on `127.0.0.1:55432`. Removed afterward. The Compose catalog was not used.

| Command | Result |
| --- | --- |
| `pytest tests/test_pricing.py tests/test_public_catalog.py` | 13 passed |
| `npm run typecheck` in `web/` | Passed |
| `node --experimental-strip-types --test` on `web/src/lib/*.test.mts` | 32 passed |

Covered: both workbook factors, HiLook via `hikvision`, half-up and decimal precision, on-request, hidden, unavailable, no double conversion, stored USD unchanged after a public read, UZS filters and sort, three-language formatting, selection totals with exclusions, and existing selection slug behavior.

## Docker site (port 8080)

Rebuilt only `api` and `web`:

```text
docker compose --env-file .env -f docker-compose.yml -f docker-compose.dev.yml up -d --no-deps --build api web
docker compose ... exec nginx nginx -s reload
```

Containers after verification:

| Service | Container id (short) | Notes |
| --- | --- | --- |
| api | `3814f83ef46a` | Recreated; healthy |
| web | `546fb3d6c098` | Recreated; healthy |
| postgres | `747524f4819c` | Unchanged since earlier today |
| nginx | `d2b45c32481e` | Unchanged; config reloaded only |

Named volumes `camera-shop_postgres_data` and `camera-shop_catalog_media` stayed mounted. No migration. No workbook apply. No catalog row rewrite. No credential change.

### API checks

| Check | Result |
| --- | --- |
| `GET /api/health` | `{"status":"ok","database":"ok"}` |
| Published products | `total: 639` |
| Provenance | 555 `hikvision`, 84 `ezviz` |
| `product-12v-10a` | stored 4.00 USD / hikvision → display `38400` UZS |
| `hilook-ipc-b469had-luf-sl` | stored 115.00 USD / hikvision → display `1104000` UZS |
| `ezviz-cs-c60p-3mp` | stored 50.00 USD / ezviz → display `540000` UZS |
| Soʻm filter `min_price=38000&max_price=39000` | Includes `product-12v-10a` at 38400 UZS |
| `/ru/checkout`, `/ru/cart` | 404 |

Stored USD confirmed by a read-only SQL select on those three slugs. Amounts and currencies were unchanged after the rebuild.

### Browser checks on `http://127.0.0.1:8080`

| Page | Observed |
| --- | --- |
| HiLook product | `1 104 000 сум`; add toggled header to `Подборка 1` |
| EZVIZ brand list | Cards show soʻm (for example `54 000 сум`, `540 000 сум`); no USD |
| Selection (HiLook + EZVIZ monthly) | `Итого : 1 158 000 сум` (= 1 104 000 + 54 000) |
| Selection + WD on-request | Still `1 158 000 сум`; disclosure `Сумма без товаров по запросу и без цены.`; WD shown as `По запросу` |
| Footer | States that order and payment are not placed on the site |

## Remaining gaps (outside Phase 6 scope)

- Admin price editing still shows and writes USD, as required.
- Currency label strings are duplicated in `price-format.ts` and `public-i18n.ts` so Node library tests stay free of path aliases.
- Phase 5 signed-in admin checks and Phase 3 authorized login/logout on port 8080 remain open (credentials not reset).
- Phase 8 production inputs (domain, TLS, `PUBLIC_SITE_URL`, contact details, scheduled backups) remain open. See `docs/production-readiness-report.md`.

## Verdict

Phase 6 is complete for the local Docker site on port 8080.
