# SEO audit — HikVision catalog

**Date:** 19 October 2026
**Checkpoint:** `3b6b1c15133c1fa14acbc68589089da3b1f52c8a` (`Polish multilingual catalog, cart, and SEO`)
**Branch:** `main` (synced with `origin/main` at audit time)
**Scope:** Read-only SEO audit of the Next.js public site, SEO helpers, sitemap/robots, nginx reverse proxy, and live local Docker HTTP/API responses.
**Constraint:** No application code, configuration, database data, translations, imports, migrations, commits, pushes, or deployments were modified. The prior report `docs/multilingual-catalog-audit.md` was not overwritten or edited.

**Local origin under test:** `http://127.0.0.1:8080` (nginx → web/api).
**Configured `PUBLIC_SITE_URL`:** loopback placeholder (`http://localhost` / equivalent). Loopback hosts are intentionally rejected by `publicOrigin()` in `web/src/lib/seo.ts`, so absolute canonicals, head `hreflang`, sitemap hosts, absolute Open Graph URLs, and absolute JSON-LD site/image URLs are omitted on this environment.

**Not verified:** Google Search Console, Bing Webmaster, live crawl budget, production HTTPS, or real public rankings. No production domain was invented.

---

## A. Executive summary and readiness

The catalog has a solid **technical SEO foundation in source**: locale-prefixed routes (`ru` / `uz` / `en`), server-rendered titles and H1s, listing `noindex` for filters/search/pagination, admin `noindex,nofollow`, Product JSON-LD with UZS offers, Organization JSON-LD, sitemap data API covering published catalog URLs, and legacy `/{locale}/selection` → `/{locale}/cart` redirects.

**Local SEO readiness:** suitable for development verification only. With the loopback placeholder, `/sitemap.xml` is an empty urlset, head canonical/`hreflang` are absent, and robots.txt omits the Sitemap line — **by design**, not a local regression.

**Production SEO readiness:** **not ready to expose to search engines** until a real non-loopback HTTPS `PUBLIC_SITE_URL` is set and re-verified. Beyond that gate, the highest content/title issues are duplicated brand segments in product `<title>` tags (~437 products with `— Hikvision|HikVision`-style redundancy, including 96 exact `— HikVision | HikVision`), Cyrillic names leaking into UZ/EN titles (24 products), and some Russian image `alt` text on English pages.

Overall: **implementation is launch-oriented and mostly correct; production indexing is blocked on domain configuration; a small set of title/alt/content issues should be fixed before or right after go-live.**

---

## B–C. Findings by severity

### Critical

#### C1. Production absolute SEO URLs unavailable until real `PUBLIC_SITE_URL`

| Field | Detail |
| --- | --- |
| **Route / file** | `web/src/lib/seo.ts` (`publicOrigin`), `web/src/app/sitemap.ts`, `web/src/app/robots.ts` |
| **Evidence** | Live `GET /sitemap.xml` → 200 with empty `<urlset>`. Live page heads for `/en`, `/en/catalog`, `/en/products/...` have **0** `rel=canonical` and **0** head `hreflang`. Live `/robots.txt` has no `Sitemap:` line. Code returns `[]` from sitemap and omits `alternates` when origin is null/loopback. |
| **Locales / pages** | All public indexable types |
| **Impact** | Search engines cannot receive a host-correct sitemap or self-referencing canonical/`hreflang` graph. Social crawlers lack absolute `og:url` / `og:image`. |
| **Recommended fix** | After the client supplies the real HTTPS origin: set `PUBLIC_SITE_URL` (and media public base), rebuild/restart web, confirm populated sitemap, head canonicals, `hreflang` including `x-default`→RU, and Sitemap line in robots. Do not point production at localhost. |
| **Confidence** | High (live HTTP + source) |
| **Note** | This is **intentional local behavior**. It is critical for **production launch**, not a local bug. |

---

### High

#### H1. Product `<title>` repeats the site/brand name

| Field | Detail |
| --- | --- |
| **Route / file** | `web/src/lib/product-seo.ts` (`productTitle`), used by `web/src/app/[locale]/products/[slug]/page.tsx` |
| **Evidence** | Formula is `{name} — {brand\|\|HikVision} \| HikVision`. Live `/en/products/product-gibkiy-perekhod` title: `Flexible transition — HikVision \| HikVision`. API aggregate over 639 published products (EN): **96** exact `— HikVision \| HikVision` (null/missing brand falls back to site name). **341** additional titles use brand label `Hikvision` → `— Hikvision \| HikVision` (near-duplicate casing). Brand name histogram: Hikvision 341, HikVision-fallback/null 96, HiLook 106, EZVIZ 84, others smaller. |
| **Locales / pages** | Product detail, all locales (same pattern) |
| **Impact** | Bloated, awkward SERP titles; weaker differentiation; looks unpolished for the largest brand cohort. |
| **Recommended fix** | When brand name case-insensitively equals `HikVision`/`Hikvision`, or brand is absent, emit `{name} \| HikVision` (or `{name} (model) \| HikVision`) once. Keep `{name} — {OtherBrand} \| HikVision` for EZVIZ/HiLook/etc. |
| **Confidence** | High |

#### H2. Cyrillic product names in UZ/EN metadata titles

| Field | Detail |
| --- | --- |
| **Route / file** | Product translations / `productTitle` using API `name` |
| **Evidence** | Programmatic check of all 639 products via `/api/public/products/{slug}?locale=`: **24** UZ and **24** EN products have Cyrillic in `name`, so generated titles are Russian on non-Russian locales. Examples: `ezviz-30-dnevnaya-videoistoriya-sobytiy-ezhegodno`, `ezviz-cs-sd7-umnyy-ekran`. Overlaps the multilingual catalog audit content finding. |
| **Locales / pages** | UZ/EN product detail `<title>`, OG title, visible H1 |
| **Impact** | Wrong-language SERP snippets for those URLs; weak UZ/EN relevance signals. |
| **Recommended fix** | Supply UZ/EN `localized_name` (or acceptable Latin fallbacks) for the 24 products; re-audit titles. |
| **Confidence** | High |

#### H3. Cyrillic / non-localized image `alt` on English pages

| Field | Detail |
| --- | --- |
| **Route / file** | `api/app/public/router.py` `_image` (`alt_text` or product-name fallback); rendered by `ProductPhoto` |
| **Evidence** | Live `/en/products/product-gibkiy-perekhod` primary image `alt="гибкий переход"`. Across EN product image payloads: **15** images with Cyrillic `alt` (samples: EZVIZ cloud-history alts, `Блок розеток`, `Брелок`). Catalog listing on `/en/catalog` also showed `EZVIZ 7-дневная видеоистория событий` as an alt. Empty alts on primary listing images: 0 in the EN image payload count. |
| **Locales / pages** | EN (and likely UZ) product/listing images |
| **Impact** | Accessibility and image-search relevance mismatch for non-Russian locales. |
| **Recommended fix** | Prefer locale-appropriate alt (localized name / model); avoid shipping Russian alt_text unchanged on UZ/EN when a localized name exists. |
| **Confidence** | High for samples + EN aggregate count; not every HTML listing page was browser-walked. |

#### H4. Strategy documentation drift vs live implementation

| Field | Detail |
| --- | --- |
| **Route / file** | `docs/seo-strategy.md`, `docs/PROJECT_HANDOFF.md` (Phase 7 notes) vs `web/src/lib/seo.ts` / `product-seo.ts` |
| **Evidence** | Strategy still describes product titles as `{model} — {brand} \| HikVision` and Product offers `priceCurrency = USD`. Live titles use **localized name** (post-checkpoint SEO work). Live Product JSON-LD offers use **`UZS`** (e.g. `"price":"14400","priceCurrency":"UZS"` on `/en/products/product-gibkiy-perekhod`). Handoff text still mentions numeric USD offers from an older Phase 7 fixture run. |
| **Locales / pages** | Docs vs all product pages |
| **Impact** | Operators may “fix” the wrong currency or title formula; audit/remediation confusion. |
| **Recommended fix** | Update strategy/handoff to match name-based titles and UZS offers (no code change required for SEO correctness). |
| **Confidence** | High |

---

### Medium

#### M1. `robots.txt` allows cart (and other noindex) paths

| Field | Detail |
| --- | --- |
| **Route / file** | `web/src/app/robots.ts`; live `/robots.txt` |
| **Evidence** | Allows `/ru`, `/uz`, `/en` (prefix). Disallows `/admin`, `/api/`, `/media/imports`, `/media/private-uploads`. Does **not** disallow `/cart`, `/search`, or `/products`. Cart/search/products pages correctly send `noindex, follow` in HTML. |
| **Locales / pages** | `/{locale}/cart`, `/{locale}/search`, `/{locale}/products` |
| **Impact** | Crawlers may fetch noindex URLs (waste). Risk is low because meta robots is set; not an indexing leak if respected. |
| **Recommended fix** | Optional: add `Disallow` for `/ru/cart`, `/uz/cart`, `/en/cart` (and optionally search) after confirming it does not block needed CSS/JS (these are HTML routes only). |
| **Confidence** | High |

#### M2. Brand index titles look like doubled brand

| Field | Detail |
| --- | --- |
| **Route / file** | `namedTitle` → `{name} \| HikVision`; live `/ru/brands/hikvision` → `Hikvision \| HikVision` |
| **Evidence** | Live title `Hikvision \| HikVision` with `index, follow`. |
| **Locales / pages** | Brand detail pages |
| **Impact** | Mild SERP awkwardness for the Hikvision brand URL. |
| **Recommended fix** | Special-case when entity name ≈ site name: use `Hikvision catalog \| HikVision` or site name alone. |
| **Confidence** | High |

#### M3. Open Graph `og:type` is always `website`

| Field | Detail |
| --- | --- |
| **Route / file** | `pageMetadata` in `web/src/lib/seo.ts` |
| **Evidence** | Product page head includes `property="og:type" content="website"`. |
| **Locales / pages** | Product (and all) pages |
| **Impact** | Minor; Product JSON-LD carries product semantics. Some social parsers prefer `og:type=product` (non-standard in OG but used commercially). |
| **Recommended fix** | Optionally set product pages to a product-oriented OG type if desired; low priority vs domain/titles. |
| **Confidence** | High |

#### M4. Admin inherits generic root meta description

| Field | Detail |
| --- | --- |
| **Route / file** | `web/src/app/layout.tsx` default description; `web/src/app/admin/layout.tsx` sets title + robots only |
| **Evidence** | Live `/admin/login`: title `HikVision admin`, robots `noindex, nofollow`, description `Informational product catalog`. |
| **Locales / pages** | Admin |
| **Impact** | Negligible for SEO (noindex); slightly noisy if a stub is ever indexed contrary to robots. |
| **Recommended fix** | Set an explicit admin description or empty description in admin layout. |
| **Confidence** | High |

#### M5. Language-switcher `hrefLang` is not head `hreflang`

| Field | Detail |
| --- | --- |
| **Route / file** | `web/src/components/public/language-switcher.tsx`, `site-header.tsx` |
| **Evidence** | Body contains `hrefLang="ru|uz|en"` on nav links. Head has **no** `link rel="alternate" hreflang` while origin is loopback. When origin is set, head alternates come from `pageMetadata` only. |
| **Locales / pages** | All public pages |
| **Impact** | Body `hrefLang` does not replace SEO alternate link tags. Fine for UX; do not treat switcher links as proof that SEO hreflang is active locally. |
| **Recommended fix** | None required for switcher; verify head tags after production origin is configured. |
| **Confidence** | High |

---

### Low

#### L1. Decorative / UI images intentionally use empty `alt`

| Field | Detail |
| --- | --- |
| **Route / file** | `product-gallery.tsx` thumbnails `alt=""`; `home-search.tsx` suggestion thumbs `alt=""` |
| **Evidence** | Source inspection; primary gallery image uses real alt. |
| **Impact** | Acceptable if adjacent text names the product; ensure primary image keeps a meaningful alt. |
| **Recommended fix** | Keep; optionally mirror primary alt on thumbnails if desired. |
| **Confidence** | Medium–high |

#### L2. Product JSON-LD omits `InStock` and absolute images locally

| Field | Detail |
| --- | --- |
| **Route / file** | `productJson` in `web/src/lib/seo.ts` |
| **Evidence** | Live product JSON-LD has Offer with UZS price and **no** `availability` when in stock (0 products `out_of_stock` in API aggregate). Images omitted from JSON-LD without public origin. Strategy documents this stock policy. |
| **Impact** | By design for stock; images unlock with production origin. |
| **Recommended fix** | None for stock policy; re-check image absolute URLs after `PUBLIC_SITE_URL`. |
| **Confidence** | High |

#### L3. Homepage title is company name only

| Field | Detail |
| --- | --- |
| **Route / file** | `web/src/app/[locale]/page.tsx` → `title: company.name` |
| **Evidence** | Live `/en` title `HikVision`; description `HikVision. Catalog`. |
| **Impact** | Short but on-brand; acceptable. |
| **Recommended fix** | Optional richer title if marketing wants “HikVision — video surveillance catalog”. |
| **Confidence** | High |

---

### Informational

#### I1. Indexability policy matches strategy for listings

- Clean `/catalog`, category, brand, home, contact: `index, follow` (sampled).
- `?brand=`, `?q=`, `?page=2`, `/search`, `/products`: `noindex, follow` (sampled).
- `/products` metadata `path` points at `/{locale}/catalog` so that, with a real origin, canonical consolidates to catalog (code in `products/page.tsx`).

#### I2. Sitemap API coverage (expected once origin is set)

| Kind | Count (entries, all locales) |
| --- | --- |
| Home | 3 |
| Catalog | 3 |
| Categories index | 3 |
| Contact | 3 |
| Category detail | 144 (48 × 3) |
| Brand | 21 (7 × 3) |
| Product | 1917 (639 × 3) |
| **Total** | **2094** unique paths |
| Local `/sitemap.xml` | **0** URLs (empty urlset) |

Cart, selection, search, admin, API paths: **absent** from sitemap API (verified). Published product count matches public list total **639**.

#### I3. Crawl / status samples (local)

| Check | Result |
| --- | --- |
| `/` | 307 → `/ru` |
| `/ru`, `/uz`, `/en` | 200 |
| Catalog / categories / products / contact | 200 |
| Missing product / invalid locale | 404 |
| `/{locale}/selection` | 307 → `/{locale}/cart` |
| Admin / login | 200 + `noindex, nofollow` |
| `html lang` | Matches locale on sampled pages |
| Catalog product links | Crawlable `<a href="/en/products/...">` (24 unique on first page); H2 names in SSR HTML |

#### I4. Structured data present

- Homepage: Organization (`name` only locally; no `url` without origin).
- Product: Product + Offer (UZS when numeric); BreadcrumbList **null** locally (needs origin).
- Contact: Organization JSON-LD present (sampled count 2 script tags including page wiring).
- WebSite/SearchAction: omitted locally (needs origin).

#### I5. Related multilingual content debt

See `docs/multilingual-catalog-audit.md` for translation coverage. SEO titles inherit those content gaps (H2).

---

## D. Aggregate checks and counts

| Metric | Result |
| --- | --- |
| Published products (API / sitemap) | 639 |
| Public categories in sitemap (per locale) | 48 |
| Brands in sitemap (per locale) | 7 |
| Expected sitemap URLs with real origin | 2094 |
| Live sitemap URLs on loopback | 0 |
| Static page empty `<title>` (home/catalog/categories/contact × 3 locales) | 0 |
| Static page empty meta description (same set) | 0 |
| Exact double `HikVision \| HikVision` product titles (EN formula) | 96 |
| Near-duplicate Hikvision/HikVision product titles (EN) | 437 |
| Cyrillic `name` → UZ titles | 24 |
| Cyrillic `name` → EN titles | 24 |
| EN product images with Cyrillic alt | 15 |
| Numeric UZS offer-eligible products | 587 |
| On-request (no Offer) | 52 |
| Out-of-stock flags | 0 |
| Head canonical on loopback samples | 0 |
| Head hreflang on loopback samples | 0 |
| Google indexing / rankings | **Not verified** |

Representative live titles:

| URL | Title | Robots |
| --- | --- | --- |
| `/en` | HikVision | index, follow |
| `/ru/catalog` | Каталог \| HikVision | index, follow |
| `/en/catalog?brand=hikvision` | Catalog \| HikVision | noindex, follow |
| `/en/products` | Products \| HikVision | noindex, follow |
| `/en/cart` | Cart \| HikVision | noindex, follow |
| `/en/products/product-gibkiy-perekhod` | Flexible transition — HikVision \| HikVision | index, follow |
| `/uz/categories/drugie-ustroystva` | Boshqa qurilmalar \| HikVision | index, follow |
| `/admin/login` | HikVision admin | noindex, nofollow |

---

## E. Local verification vs production (cannot complete without real HTTPS domain)

| Check | Local (`127.0.0.1:8080`) | Needs production HTTPS origin |
| --- | --- | --- |
| Titles / descriptions / robots meta | Verified | Re-spot-check |
| Absolute canonical | Omitted (expected) | Required |
| Head hreflang + x-default | Omitted (expected) | Required |
| Populated `/sitemap.xml` | Empty (expected) | Required; expect ~2094 URLs |
| robots `Sitemap:` line | Absent (expected) | Required |
| Absolute `og:url` / `og:image` | Absent (expected) | Required |
| JSON-LD `image` / WebSite url / breadcrumb item URLs | Absent (expected) | Required |
| HTTPS, HSTS, www/apex 301 | HTTP-only nginx (`deploy/nginx.conf`) | Required |
| Search Console property / sitemap submit | N/A | Required for indexing proof |
| External link equity / rankings | N/A | Not claimed |

---

## F. Prioritized remediation plan

### Safe code/content fixes (no production domain required)

1. **Deduplicate product title brand segment** (`product-seo.ts`) — fixes H1 for ~96–437 URLs.
2. **Add UZ/EN localized names** for the 24 Cyrillic-title products — fixes H2 (content; may already be tracked in multilingual audit).
3. **Normalize image alt** for non-RU locales — fixes H3.
4. **Align `docs/seo-strategy.md` / handoff** with name-based titles and UZS offers — fixes H4.
5. Optional: brand-page title special case (M2); admin description (M4); robots Disallow cart (M1).

### Requires production-domain / business decision

1. Client supplies real HTTPS host (apex vs www).
2. Set `PUBLIC_SITE_URL` and `MEDIA_PUBLIC_BASE_URL` to that origin; TLS/HSTS on nginx.
3. Verify non-empty sitemap, head canonical/`hreflang`, OG absolutes, JSON-LD images.
4. Submit sitemap in Search Console; monitor coverage (outside this audit).
5. Decide whether to Disallow cart/search in robots vs meta-noindex only.

**Do not** treat localhost or `127.0.0.1:8080` as a public canonical host.

---

## G. Methods, endpoints, and limitations

### Commands / endpoints used (read-only)

- `git rev-parse HEAD`, `git status` — confirm checkpoint and clean app tree aside from untracked audits.
- Docker Compose health via `docker compose ps` — api/web/nginx/postgres healthy.
- HTTP: `http://127.0.0.1:8080` paths including `/`, `/{locale}`, catalog/categories/products/brands/cart/contact/search/admin, `/robots.txt`, `/sitemap.xml`, legacy `/selection`.
- API: `GET /api/public/sitemap`, `GET /api/public/products/{slug}?locale=`, product list total.
- Python one-off scripts (stdlib `urllib`) for status matrices, metadata parsing, title/alt aggregates, sitemap kind counts. No DB writes, no admin mutations.

### Source files reviewed

- `web/src/lib/seo.ts`, `web/src/lib/product-seo.ts`
- `web/src/app/sitemap.ts`, `robots.ts`, root/`[locale]` layouts and public pages (home, catalog, products, categories, brands, search, cart, contact, selection redirect)
- `api/app/public/router.py` (sitemap + image alt)
- `deploy/nginx.conf`
- `docs/seo-strategy.md`, `docs/production-readiness-report.md`, `docs/PROJECT_HANDOFF.md` (SEO sections)

### Limitations

- Not every one of 639×3 product HTML responses was fetched; title/Cyrillic/offer aggregates used the public API + the same title formula as production code. Spot HTML checks validated the formula on live pages.
- No authenticated admin crawl beyond `/admin` and `/admin/login` metadata.
- No production host, TLS, or Search Console evidence.
- Body `hrefLang` on the language switcher must not be confused with SEO head alternates.
- Image alt Cyrillic count is from API image payloads (EN), not a full rendered DOM crawl of every listing page.

### Final verification (audit hygiene)

| Check | Status |
| --- | --- |
| Application code / catalog data modified | **No** |
| Imports / migrations / commits / pushes / deploys | **No** |
| `docs/multilingual-catalog-audit.md` untouched | **Yes** (still untracked; hash at audit end `7E0D6180388A38FFDD4AEED96EDE86F338F710CEFA14CB4EF4957950D8FCCEEF`, size 14400 bytes) |
| This report | **New** file `docs/seo-audit.md` (untracked when created) |
| Git HEAD | `3b6b1c15133c1fa14acbc68589089da3b1f52c8a` |

---

*End of SEO audit.*
