# SEO strategy

Search is part of the first release for HikVision. This strategy does not promise rankings or placement. Advertising campaigns are out of scope.

Public pages are rendered on the server. The HTML includes the H1, the price state, and the description that is actually available for that locale.

The public company name is HikVision. The domain is not known yet. Canonicals, sitemap URLs, and structured-data hosts use the configured `PUBLIC_SITE_URL`. Until the client supplies the domain, that setting stays a placeholder and must be changed before launch. No host name is invented in content.

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

Two `CS-H8c (3MP)` rows must not receive the same slug. Import does not change a slug after insert. An admin change writes `slug_redirects` and every locale 301s from the old slug to the new one.

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

- One `<title>`. Prefer the locale’s `seo_title`. Otherwise `{model} — {brand or HikVision} | HikVision` for products, and `{localized category} | HikVision` for categories.
- One meta description, from `seo_description` or the fallback in the previous section. Do not invent specifications.
- One H1. Products use the localized name if one was saved, otherwise the display model.
- `<link rel="canonical">` to that locale’s own HTTPS URL.
- `hreflang` alternates for `ru`, `uz`, and `en`, plus `x-default` pointing at the Russian URL. Russian is the source language. This is a technical default, not a claim that Russian is a translation of the other locales.

Filtered and search URLs canonicalize to the unfiltered catalog or category URL for that locale. They are not indexed as separate pages.

When the real domain replaces the placeholder, canonicals and `hreflang` must all use that host, with one 301 from the other host form (`www` or apex) after the client chooses it.

## Open Graph

- `og:locale` is `ru_RU`, `uz_UZ`, or `en_US` to match the page. `og:locale:alternate` lists the other two.
- `og:title` and `og:description` follow the SEO fields.
- `og:url` is the canonical.
- `og:image` is the primary public image as an absolute HTTPS URL when a high-confidence or confirmed image exists. If there is no public image, omit `og:image`. Do not use a stock photo.
- The site name is HikVision.

## Structured data

JSON-LD in the server-rendered page.

**Product** on published product URLs:

- `name`: localized name or display model.
- `brand`: brand name when verified. Omit brand rather than inserting HikVision for an unbranded accessory.
- `description`: the locale’s description, or omit it when the page is showing the Russian original on a non-Russian URL. Do not put the fallback Russian text in an Uzbek or English `description` field.
- `image`: public image URLs.
- `sku`: the slug, because the model is not unique.
- `offers` when the public status is `numeric`: `price`, `priceCurrency` = `USD`. No discount fields. No `availability` quantity. When status is `on_request` or `hidden`, omit `offers`. Do not emit zero.
- Out of stock may add `offers.availability` = `OutOfStock` only when staff set that status and a numeric price exists. In stock omits availability. Do not mark items in stock by default inside structured data if that would claim stock the business did not confirm; omitting availability is the default. Out-of-stock is the only stock fact the business asked to show, so that is the only availability value emitted.

**BreadcrumbList** uses the locale’s labels and URLs: Home, catalog, brand or category, product.

**Organization** uses the name HikVision. Add `url`, `telephone`, `email`, and `address` only after those profile fields are non-empty. Do not ship placeholder NAP data. LocalBusiness is used instead of Organization only when a real address exists.

## Sitemap and robots

`/sitemap.xml` lists, for each locale:

- Home, catalog, and contact.
- Published brands and categories.
- Published, non-archived, non-deleted products.

It omits drafts, archived products, admin, import preview, and search URLs.

Each URL entry can include `xhtml:link` alternates for the three locales.

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
- Alt text defaults to brand plus model, or model alone.
- The primary image is the LCP candidate and includes width and height when known.
- Checksum URLs use long cache headers because the path changes when the bytes change.
- Category grids use a resized image. The product page can use a larger rendition. The extracted file remains the original.
- Layout is mobile-first. Text and tap targets must work at phone width. Core Web Vitals are protected by server-rendered content, sized images, and no blocking third-party tags at launch.

## After the domain is known

1. Set `PUBLIC_SITE_URL` to the real origin and redirect the other host form with 301.
2. Verify the property in Google Search Console and submit the sitemap.
3. Inspect one Russian product URL, its Uzbek and English alternates, and a request-price URL. Confirm H1, canonical, and `hreflang`.
4. Confirm unpublished URLs 404 and `/admin` is excluded.
5. Validate Product structured data. Confirm USD appears only on numeric prices and discount notes do not appear.
6. Add analytics only if the client approves a specific tool. It must not block rendering.
7. Create or claim a Business Profile only with the verified name and the contact details the client has actually provided.

Ranking is not a launch criterion. Stable, localized, indexable pages are.
