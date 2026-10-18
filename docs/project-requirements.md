# Project requirements

Production catalog for **HikVision**, a CCTV and security-equipment company. This document is the requirements baseline. It does not authorize application code by itself.

The company that owns the site is HikVision. Product brands in the catalog are separate. A row in `Hikvision pr.xlsx` is not assumed to be manufactured by Hikvision.

## Business goals

- Publish every legitimate product and category from both client workbooks.
- Let visitors browse brands, categories, prices, descriptions, specifications, images, and contact details in Russian, Uzbek, and English.
- Show one numeric price in Uzbek soʻm, calculated from the stored USD amount and the source workbook. Do not show a second price or a discount badge.
- Let staff correct the live catalog, including prices, translations, images, and stock, without editing Excel.
- Import either workbook, or both, without changing the source that was not uploaded and without deleting products that disappeared from a file.
- Keep internal notes, source paths, and import diagnostics off the public site.

This is an informational catalog. It is not a store.

## Confirmed client decisions

1. **Company.** The public company name is `HikVision`. The client already owns a domain; the exact domain was not provided and must not be invented. Contact details and social links are centrally managed in the admin and use placeholders until real values are confirmed.
2. **Catalog coverage.** All legitimate categories and product records from `Hikvision pr.xlsx` and `Ezviz pr.xlsx` are included. Products are not omitted because the price cell is blank or the image is missing. Services and subscriptions are identified and kept, not discarded.
3. **Repeated models.** Similar or repeated model names may be different products. They stay separate, with their own database ids and unique slugs. They are not merged or deleted automatically. Excel row numbers are provenance, not permanent ids.
4. **Brands.** Every verified brand in the source is preserved, including WD, Seagate, Andel, Cougar, EZVIZ, HiLook, and Hikvision where the source supports that brand. If the brand is unclear, the product is imported and flagged for review. The brand is not guessed.
5. **Stored currency.** Numeric public prices are stored as USD decimals. The public site does not display that USD amount. Display uses the fixed UZS formula in decision 17. There is no live exchange rate.
6. **EZVIZ initial price.** `Цена для дилера` is the initial stored public price for EZVIZ rows. It is not labeled as a dealer price. Administrators can change the stored USD amount later. The source amount and column name stay in provenance. Visitors see the EZVIZ UZS formula applied to the current stored amount.
7. **Hikvision initial price.** The main stored price is the numeric `Цена` cell. Discount text is not a stored price and is not a display price.
8. **One public price.** Visitors see one amount. The site does not show the Hilook discount notes, a crossed-out price, a discount percentage, or the stored USD amount beside the UZS amount. The factors in decision 17 are fixed display rules, not a public discount badge.
9. **Request price.** An explicit source value `По запросу` is shown as `По запросу` in Russian, with Uzbek and English equivalents. A blank source price is never stored or shown as zero. Its **public** status is initialized to the same request-price state. The import still records that the source cell was blank, so provenance is not destroyed. No numeric price is invented.
10. **Verified discount notes.** On worksheet `Hilook`, column F has no header. These cells contain notes, not the main price: `F103` and `F106` are `текущая цена со скидкой 60$`; `F107` and `F115` are `текущая цена со скидкой 100$`. They are cell values, not comments. The main prices are `E103` = 115, `E106` = 115, `E107` = 200, and `E115` = 200. Those `Цена` amounts are the initial public prices. The notes stay internal.
11. **Images.** Use the embedded workbook images. Do not substitute stock or generated images. Do not assume image order matches product order, or that every product has one image. Assign automatically only when the anchor evidence is strong. Flag ambiguous matches. Do not discard unassigned images. Leave the original workbooks unchanged. Store files outside ordinary product rows and store paths and metadata in PostgreSQL.
12. **Languages.** The public catalog and the relevant admin interface support Russian (`ru`), Uzbek (`uz`), and English (`en`). Original Russian source text is preserved. Missing translations are not presented as verified translations.
13. **Stock.** Show a localized out-of-stock label only when a product is out of stock. In-stock products have no availability badge. Do not show quantities. Do not infer stock from Excel. New products are not marked out of stock. Administrators set stock manually. Stock is independent of price.
14. **Two workbooks.** Hikvision and EZVIZ files are independent sources. An administrator can upload one file or both. A missing file does not change or delete the other source. Invalid data is not applied and is not treated as deletion. Preview does not change the live catalog. One batch action applies the approved changes.
15. **Manual edits.** The PostgreSQL catalog is the live source for the website. Imports must not silently overwrite administrator edits. The administrator can keep the current value or accept the Excel value. A batch-level option may replace prices, and the preview must show which manual prices that option overwrites.
16. **Absence is not deletion.** A product missing from a newly uploaded workbook is reported and kept. Archiving or discontinuing it is a separate explicit admin action.
17. **Displayed UZS price.** Visitors see Uzbek soʻm calculated from the current stored public USD amount and the workbook that supplied the product. The formula is not stored on the product. Manual edits continue to change the stored USD amount. A routine import still must not replace a locked public price unless the administrator enables batch price replacement. Details, rounding, and missing provenance are in the following section.
18. **Product list.** `/ru/selection`, `/uz/selection`, and `/en/selection` are a cart-like list of products. Visitors can add, view, and remove products. The list is not a checkout.

## Public website

Visitors can:

- Choose Russian, Uzbek, or English and switch language without losing their place.
- Browse brands and categories.
- Search, filter, and sort published products.
- Open a product page with the model, available translation or a clearly labeled Russian original, specifications, images, and price.
- See a numeric UZS price or the localized request-price label.
- Add a published product to the browser list, open that list, and remove it. The list keeps one entry per product and survives navigation and refresh.
- See an out-of-stock label only when staff have marked the product out of stock.
- Read the company name and whatever contact and social details staff have published.

Published pages are server-rendered. Unpublished, archived, and admin URLs are not public catalog entries.

## Admin

Administrators can:

- Sign in and sign out.
- Create, edit, publish, unpublish, and archive products.
- Edit names, descriptions, specifications, prices, and translations.
- Manage brands, categories, images, and stock status.
- Edit company contact details and social links.
- Upload one or both workbooks, review one combined preview, exclude problem rows, resolve conflicts, and apply the approved batch once.
- Read import history, errors, and results.

Excel import and manual editing write the same catalog tables.

## Displayed UZS prices

Approved 18 October 2026. This replaces public display of USD. It does not replace the stored USD amount.

The source workbook selects the formula. The product brand does not. A HiLook sheet in `Hikvision pr.xlsx` uses the Hikvision formula. `product_source_records.source_code` is the reliable field: `hikvision` or `ezviz`. The worksheet name, the brand, and the original filename are not substitutes when `source_code` is missing.

| Workbook | `source_code` | Displayed price |
| --- | --- | --- |
| `Hikvision pr.xlsx` | `hikvision` | `stored_usd * 12000 * 0.8` |
| `Ezviz pr.xlsx` | `ezviz` | `stored_usd * 12000 * 0.9` |

Examples, using the stored USD amount:

- Hikvision workbook, 500 USD → 4,800,000 UZS.
- EZVIZ workbook, 500 USD → 5,400,000 UZS.
- Hikvision workbook, Hilook row E103, 115 USD → 1,104,000 UZS. The column F note is not an input.

Calculate with `decimal.Decimal`, never binary floating point. `12000 * 0.8` is exactly `9600`. `12000 * 0.9` is exactly `10800`. Quantize the result to a whole soʻm with half-up rounding. For a stored `numeric(12,2)` amount those factors already produce a whole number, so rounding does not change it.

The same function supplies cards, search suggestions, product pages, the browser list, list totals, public price filters, and structured data. The browser list adds the returned whole-soʻm amounts. It does not apply a second formula.

Public labels:

| Locale | Currency label | Grouping example |
| --- | --- | --- |
| Russian | `сум` | `4 800 000 сум` |
| Uzbek | `soʻm` | `4 800 000 soʻm` |
| English | `UZS` | `4,800,000 UZS` |

The amount is the same in every language. The public site does not show `$` or `USD` for a product price.

`on_request` stays a label. A blank source cell and an explicit `По запросу` still store no amount. They must not become zero and must not receive a calculated UZS amount. `hidden` stays omitted on the public site.

If `source_code` is missing, or it is not `hikvision` or `ezviz`, do not choose a formula. A numeric stored price in that state is not shown as USD and is not given a guessed UZS amount. The public state is unavailable. On 18 October 2026 a read-only check found no such product: all 639 published products have one source row, 555 `hikvision` with workbook `Hikvision pr.xlsx` and header `Цена`, and 84 `ezviz` with workbook `Ezviz pr.xlsx` and header `Цена для дилера`. No schema change is required for that catalog. A product created only in the admin has no source row until an import attaches one. Leave that price unavailable rather than adding a column or guessing from the brand.

Imports keep writing the stored USD amount. `price_locked` and `replace_prices` are unchanged. The display formula is applied when a public response is built, not by overwriting `public_price_amount`.

Public minimum and maximum price filters use the displayed soʻm amount. They compare against the same formula in the query. They do not ask visitors to type USD.

The admin editor continues to read and write the stored USD amount. It may show the calculated soʻm as a preview of the public price.

## Product list

The existing pages `/ru/selection`, `/uz/selection`, and `/en/selection` become the cart-like list. Keep the browser `localStorage` list of product slugs. There is no account and no server cart. The list holds at most 50 products, which is the limit already implemented.

Required behavior:

- Add a product, view the list, and remove a product.
- The same product appears once.
- The list survives navigation and refresh in that browser.
- Each row shows the localized title, the model, and the displayed UZS price.
- A combined total sums only rows with a numeric UZS amount.
- A product priced on request may stay in the list. It adds nothing to the total. When any such row is present, the page says that the total excludes request-price products.
- A numeric product with no reliable workbook also adds nothing. The same disclosure covers it. Do not invent a soʻm amount for it.
- If every row is excluded, do not show a total of zero.
- A slug that is unpublished, archived, or deleted is removed from the stored list when the public product request returns 404. A failed request leaves that row in place and does not count it as zero.
- Titles and prices are read from the catalog when the list opens. The stored list does not freeze an old price.
- Russian, Uzbek, and English each have localized labels, including the currency label and the total disclosure.
- Controls are buttons or links with visible names, keyboard focus, and a layout that fits a narrow screen.
- There is no checkout, payment, order submission, stock reservation, or other purchasing step.

## Non-functional requirements

- Original Russian descriptions are stored exactly, aside from leading and trailing whitespace.
- The same file and the same approved choices produce the same classifications.
- A failed or rejected import does not leave the live catalog half-updated.
- Public and admin responses use separate schemas.
- Passwords are hashed. Sessions are server-side. Admin operations check authentication and authorization on the server.
- Product URLs stay stable. A slug change redirects from the old slug.
- Each public locale has canonical and `hreflang` links.
- The catalog is hundreds to a few thousand products. PostgreSQL is the only application database.
- Deployment is Docker, Nginx, and HTTPS on the existing Ahost VPS.

## Explicit non-requirements

- Checkout, online payment, order submission, stock reservation, customer accounts, and order management. The browser product list in decision 18 does not add any of those steps.
- Quantity on hand, a promotional discount engine, or a price-history ledger.
- A live exchange-rate service, or a second stored currency. The fixed UZS display formula is required. The stored numeric amount remains USD.
- Google Sheets or an AI service in the import path.
- Microservices, Kubernetes, Kafka, Redis, or Celery.
- A guaranteed search ranking.

## Acceptance baseline

- An approved first import loads legitimate products and categories from both workbooks.
- EZVIZ stored public prices start from `Цена для дилера` in USD. Visitors see those amounts through the EZVIZ UZS formula.
- Hilook stored public prices for the four noted rows are 115, 115, 200, and 200 USD, not 60 or 100. Visitors see those stored amounts through the Hikvision UZS formula.
- Explicit `По запросу` and blank prices both start as the public request-price state, and blank is not zero.
- Repeated models remain separate records with different URLs.
- Uploading only one workbook does not change the other source.
- Re-importing an unchanged file does not duplicate products.
- Locked manual values survive unless the administrator accepts the Excel value.
- Products missing from a file remain in the catalog.
- Ambiguous images are retained for review and are not published as confirmed photos.
- A public numeric price uses the workbook formula: Hikvision 500 USD displays as 4,800,000 soʻm, and EZVIZ 500 USD displays as 5,400,000 soʻm. The stored USD amounts remain 500.
- The browser list shows those soʻm amounts, sums only numeric rows, and says when request-price rows are excluded.
- A public response cannot contain discount notes, the stored USD amount, source-column labels, server paths, or import diagnostics.
- Russian, Uzbek, and English routes render localized interface text. Untranslated product copy is labeled as the Russian original.
