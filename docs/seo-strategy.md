# SEO strategy

Search is part of the first release for HikVision. This strategy does not promise rankings or placement. Advertising campaigns are out of scope.

Public pages are rendered on the server. The HTML includes the H1, the price state, and the description that is actually available for that locale.

The public company name is HikVision. The domain is not known yet. Canonicals, sitemap URLs, and structured-data hosts use `PUBLIC_SITE_URL` only when it is an `http` or `https` origin whose host is not `localhost`, `127.0.0.1`, or `::1`, and whose path is empty. The repository value `http://localhost` is that placeholder. While it is in place, pages still have titles, descriptions, and robots directives, and they do not emit localhost as a canonical, hreflang, Open Graph, or sitemap host. Set the real origin before launch. No host name is invented in content.

## Multilingual URLs

| Page | Path |
| --- | --- |
| Home | `/{locale}` |
| Catalog | `/{locale}/catalog` |
| Brand | `/{locale}/brands/{brand-slug}` |
| Category | `/{locale}/categories/{category-slug}` |
| Nested category | `/{locale}/categories/{parent-slug}/{category-slug}` |
| Product | `/{locale}/products/{product-slug}` |
| Contact | `/{locale}/contact` |
| Search | `/{locale}/search?q=` |

`locale` is `ru`, `uz`, or `en`. `/` redirects to `/ru`.

The slug is language-neutral and stable. The same product keeps the same slug in every locale, so `hreflang` alternates differ only by the prefix. Product ids are not in the URL.

Slug algorithm, once, at insert:

1. Brand slug, or the word `product` when the brand is not verified yet, then the model slug.
2. Latin model codes stay Latin. Russian names, including the cloud-history plans, use a fixed transliteration table.
3. If `option_label` is set, append its slug so monthly and yearly plans cannot share a URL.
4. If the slug is taken, append `-r` and the source row, then the product id if needed.

Two `CS-H8c (3MP)` rows must not receive the same slug. Import does not change a slug after insert. The admin API also assigns a slug once and does not change it. `slug_redirects` is not created. A published slug does not move, so there is no old URL to redirect. If a later change allows a slug edit, that change must write a redirect row and 301 every locale from the old slug to the new one. Redirects must stay inside the public catalog and must not loop.

Admin stays at `/admin` with no locale prefix in the public sitemap. Admin screens still use `ru`, `uz`, and `en` message catalogs.

## Language switcher and fallback

The switcher links to the same path with another locale prefix.

Interface strings exist for all three locales: navigation, buttons, forms, validation, errors, the request-price label, and the out-of-stock label.

| Locale | Request-price label | Out-of-stock label |
| --- | --- | --- |
| `ru` | По запросу | Нет в наличии |
| `uz` | So'rov asosida | Mavjud emas |
| `en` | On request | Out of stock |

Uzbek interface copy uses Latin script. In-stock products show no stock phrase.

Product descriptions:

- `ru` uses the original Russian workbook text.
- `uz` and `en` use only text an administrator saved for that locale.
- If the requested locale has no description, the page shows the Russian original under a caption that is translated in the UI (“Original description (Russian)” and its Uzbek and English equivalents). The caption makes clear it is not an Uzbek or English translation.
- Meta descriptions follow the same rule. A missing Uzbek description does not become a Russian sentence presented as Uzbek. The meta description then uses the localized template: brand (if published), model, and localized category name. The model code is language-neutral and is not a fabricated specification.

`html lang` is `ru`, `uz`, or `en` to match the route.

## Titles, descriptions, canonical, hreflang

Each indexable URL has:

- One `<title>`. Prefer the locale’s `seo_title`. Otherwise products use the localized name (or display model): `{name} — {brand} | HikVision` when the brand is a distinct manufacturer, or `{name} | HikVision` when the brand is missing or matches the site name (any common casing of HikVision/Hikvision). A distinct equipment model code may appear as `{name} ({model})` only when it differs from the name and looks like a model token, not a translated phrase. Categories use `{localized category} | HikVision`.
- One meta description, from `seo_description` or the fallback in the previous section. Do not invent specifications.
- One H1. Products use the localized name if one was saved, otherwise the display model.
- `<link rel="canonical">` to that locale’s own URL on the configured public origin. The tag is omitted while the origin is still the loopback placeholder.
- `hreflang` alternates for `ru`, `uz`, and `en`, plus `x-default` pointing at the Russian URL. Russian is the source language. This is a technical default, not a claim that Russian is a translation of the other locales. The same slug exists in every locale. A missing translation still has a route and shows the Russian text on the page with the fallback caption. The meta description does not reuse that Russian sentence. These alternates are omitted while the origin is the loopback placeholder, so they are not pointed at localhost.

The first page of `/catalog`, a category, or a brand, with no query, is indexable and canonical to itself. Search, filters, sort, and later pages are `noindex, follow` and canonical to their own URL, including the query. They are not canonicalized to the unfiltered listing, because that listing is different content. `/{locale}/products` is the same listing as `/{locale}/catalog`, so it is `noindex` and canonical to the catalog. The sitemap lists only the clean indexable URLs.

When the real domain replaces the placeholder, canonicals and `hreflang` must all use that host, with one 301 from the other host form (`www` or apex) after the client chooses it.

## Open Graph

- `og:locale` is `ru_RU`, `uz_UZ`, or `en_US` to match the page. `og:locale:alternate` lists the other two.
- `og:title` and `og:description` follow the SEO fields.
- `og:url` is the canonical.
- `og:image` is the primary public image as an absolute URL on the configured origin when a high-confidence or confirmed image exists. If there is no public image, or the origin is still the loopback placeholder, omit `og:image`. Do not use a stock photo or an invented logo. Width and height are included when the image row has them.
- The site name is HikVision.

## Structured data

JSON-LD in the server-rendered page.

**Product** on published product URLs:

- `name`: localized name or display model.
- `brand`: brand name when verified. Omit brand rather than inserting HikVision for an unbranded accessory.
- `description`: the locale’s description, or omit it when the page is showing the Russian original on a non-Russian URL. Do not put the fallback Russian text in an Uzbek or English `description` field.
- `image`: public image URLs.
- `sku`: the slug, because the model is not unique.
- `offers` when the public status is `numeric`: `price`, `priceCurrency` = `UZS` (the same displayed soʻm amount as the page). Stored catalog amounts remain USD in the database and admin; public JSON-LD must not advertise USD. No discount fields. No `availability` quantity. When status is `on_request` or `hidden`, omit `offers`. Do not emit zero.
- Out of stock may add `offers.availability` = `OutOfStock` only when staff set that status and a numeric price exists. In stock omits availability. Do not mark items in stock by default inside structured data if that would claim stock the business did not confirm; omitting availability is the default. Out-of-stock is the only stock fact the business asked to show, so that is the only availability value emitted.

**BreadcrumbList** uses the locale’s labels and URLs: Home, catalog, brand or category, product.

**Organization** uses the configured public company name. Add `url` only when the public origin is configured. Add `telephone`, `email`, `address`, `logo`, and `sameAs` only when those profile fields are non-empty and, for the logo and site URL, the public origin is configured. Do not ship placeholder NAP data. LocalBusiness is used instead of Organization only when a real address exists. Ratings, reviews, and a street address are omitted when they are unknown.

**WebSite** and **SearchAction** are added on the homepage only when the public origin is configured. The target is `/{locale}/search?q={search_term_string}`, which matches the search form.

## Sitemap and robots

`/sitemap.xml` lists, for each locale:

- Home, catalog, and contact.
- Published brands and categories.
- Published, non-archived, non-deleted products.

It omits drafts, archived products, admin, import preview, and search URLs.

Each URL entry can include `xhtml:link` alternates for the three locales and `x-default`. `lastmod` is written only from the row `updated_at` for a product, category, or brand. Home, catalog, the category index, and contact omit `lastmod`. The sitemap is empty while `PUBLIC_SITE_URL` is the loopback placeholder, and `/robots.txt` then omits the Sitemap line. With a real origin, the Sitemap line is `{origin}/sitemap.xml`. `robots.txt` allows `/ru`, `/uz`, and `/en`, and disallows `/admin`, `/api/`, `/media/imports`, and `/media/private-uploads`. That file is not an access control. Authentication and publication filtering stay authoritative. Full-text search through `search_vector` is deferred; public search stays bounded `ILIKE`.

`/robots.txt`:

- Allow `/ru/`, `/uz/`, and `/en/`.
- Disallow `/admin` and `/api/`.
- `Sitemap` points at the absolute sitemap URL on the configured host.

Disallow is not an authorization control. Admin HTML is also `noindex`.

## Indexability and status codes

| Resource | Result |
| --- | --- |
| Published product, category, brand, home, contact | Indexable |
| Draft or archived product | 404. Not in the sitemap |
| Request-price product | Indexable. The page shows the localized label, not a fake number |
| Out of stock | Indexable. The badge is visible. The page is not removed just because it is out of stock |
| Service rows, if published | Indexable |
| Unknown locale or unknown slug | 404 with a useful page and links back to the locale home |
| `/admin`, `/api` | `noindex` |

Soft-deleted or archived slugs are not reused. Old slugs 301 only when a redirect row exists.

## Internal links and images

- Home links to published brands and top-level categories in the current locale.
- Brand and category pages link to their children and products.
- Product pages link to brand, category, and other published products in the same category. Same category is not a merge.
- Breadcrumbs match the structured data.
- Alt text uses the stored image alt when it is appropriate. On Uzbek and English pages, a Cyrillic stored alt (often import model text) yields to the locale product name when that name has no Cyrillic. Russian pages keep Cyrillic alts. Do not invent specifications in alt text.
- The primary image is the LCP candidate and includes width and height when known.
- Checksum URLs use long cache headers because the path changes when the bytes change.
- Category grids use a resized image. The product page can use a larger rendition. The extracted file remains the original.
- Layout is mobile-first. Text and tap targets must work at phone width. Core Web Vitals are protected by server-rendered content, sized images, and no blocking third-party tags at launch.

## After the domain is known

1. Set `PUBLIC_SITE_URL` to the real origin and redirect the other host form with 301.
2. Verify the property in Google Search Console and submit the sitemap.
3. Inspect one Russian product URL, its Uzbek and English alternates, and a request-price URL. Confirm H1, canonical, and `hreflang`.
4. Confirm unpublished URLs 404 and `/admin` is excluded.
5. Validate Product structured data. Confirm numeric offers use `UZS` (not stored USD), and discount notes do not appear.
6. Add analytics only if the client approves a specific tool. It must not block rendering.
7. Create or claim a Business Profile only with the verified name and the contact details the client has actually provided.

Ranking is not a launch criterion. Stable, localized, indexable pages are.
