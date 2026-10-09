# Project requirements

Production catalog for **HikVision**, a CCTV and security-equipment company. This document is the requirements baseline. It does not authorize application code by itself.

The company that owns the site is HikVision. Product brands in the catalog are separate. A row in `Hikvision pr.xlsx` is not assumed to be manufactured by Hikvision.

## Business goals

- Publish every legitimate product and category from both client workbooks.
- Let visitors browse brands, categories, prices, descriptions, specifications, images, and contact details in Russian, Uzbek, and English.
- Show numeric prices in USD, with no discounts.
- Let staff correct the live catalog, including prices, translations, images, and stock, without editing Excel.
- Import either workbook, or both, without changing the source that was not uploaded and without deleting products that disappeared from a file.
- Keep internal notes, source paths, and import diagnostics off the public site.

This is an informational catalog. It is not a store.

## Confirmed client decisions

1. **Company.** The public company name is `HikVision`. The client already owns a domain; the exact domain was not provided and must not be invented. Contact details and social links are centrally managed in the admin and use placeholders until real values are confirmed.
2. **Catalog coverage.** All legitimate categories and product records from `Hikvision pr.xlsx` and `Ezviz pr.xlsx` are included. Products are not omitted because the price cell is blank or the image is missing. Services and subscriptions are identified and kept, not discarded.
3. **Repeated models.** Similar or repeated model names may be different products. They stay separate, with their own database ids and unique slugs. They are not merged or deleted automatically. Excel row numbers are provenance, not permanent ids.
4. **Brands.** Every verified brand in the source is preserved, including WD, Seagate, Andel, Cougar, EZVIZ, HiLook, and Hikvision where the source supports that brand. If the brand is unclear, the product is imported and flagged for review. The brand is not guessed.
5. **Currency.** All product prices are USD. Numeric prices are stored as decimals and displayed with `$`. Values are not converted.
6. **EZVIZ initial price.** `Цена для дилера` is the initial public price for EZVIZ rows. It is shown as the product price in USD, not labeled as a dealer price. Administrators can change it later. The source amount and column name stay in provenance.
7. **Hikvision initial price.** The main price is the numeric `Цена` cell. Discount text is not a public price.
8. **No discounts.** The site shows only the main price. It does not calculate, apply, or display discounts, discount amounts, or internal discount notes.
9. **Request price.** An explicit source value `По запросу` is shown as `По запросу` in Russian, with Uzbek and English equivalents. A blank source price is never stored or shown as zero. Its **public** status is initialized to the same request-price state. The import still records that the source cell was blank, so provenance is not destroyed. No numeric price is invented.
10. **Verified discount notes.** On worksheet `Hilook`, column F has no header. These cells contain notes, not the main price: `F103` and `F106` are `текущая цена со скидкой 60$`; `F107` and `F115` are `текущая цена со скидкой 100$`. They are cell values, not comments. The main prices are `E103` = 115, `E106` = 115, `E107` = 200, and `E115` = 200. Those `Цена` amounts are the initial public prices. The notes stay internal.
11. **Images.** Use the embedded workbook images. Do not substitute stock or generated images. Do not assume image order matches product order, or that every product has one image. Assign automatically only when the anchor evidence is strong. Flag ambiguous matches. Do not discard unassigned images. Leave the original workbooks unchanged. Store files outside ordinary product rows and store paths and metadata in PostgreSQL.
12. **Languages.** The public catalog and the relevant admin interface support Russian (`ru`), Uzbek (`uz`), and English (`en`). Original Russian source text is preserved. Missing translations are not presented as verified translations.
13. **Stock.** Show a localized out-of-stock label only when a product is out of stock. In-stock products have no availability badge. Do not show quantities. Do not infer stock from Excel. New products are not marked out of stock. Administrators set stock manually. Stock is independent of price.
14. **Two workbooks.** Hikvision and EZVIZ files are independent sources. An administrator can upload one file or both. A missing file does not change or delete the other source. Invalid data is not applied and is not treated as deletion. Preview does not change the live catalog. One batch action applies the approved changes.
15. **Manual edits.** The PostgreSQL catalog is the live source for the website. Imports must not silently overwrite administrator edits. The administrator can keep the current value or accept the Excel value. A batch-level option may replace prices, and the preview must show which manual prices that option overwrites.
16. **Absence is not deletion.** A product missing from a newly uploaded workbook is reported and kept. Archiving or discontinuing it is a separate explicit admin action.

## Public website

Visitors can:

- Choose Russian, Uzbek, or English and switch language without losing their place.
- Browse brands and categories.
- Search, filter, and sort published products.
- Open a product page with the model, available translation or a clearly labeled Russian original, specifications, images, and price.
- See a numeric USD price or the localized request-price label.
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

- Shopping cart, checkout, online payment, customer accounts, and order management.
- Quantity on hand, discount engine, price-history ledger, or currency conversion.
- Google Sheets or an AI service in the import path.
- Microservices, Kubernetes, Kafka, Redis, or Celery.
- A guaranteed search ranking.

## Acceptance baseline

- An approved first import loads legitimate products and categories from both workbooks.
- EZVIZ public prices start from `Цена для дилера` and are USD.
- Hilook public prices for the four noted rows are 115, 115, 200, and 200 USD, not 60 or 100.
- Explicit `По запросу` and blank prices both start as the public request-price state, and blank is not zero.
- Repeated models remain separate records with different URLs.
- Uploading only one workbook does not change the other source.
- Re-importing an unchanged file does not duplicate products.
- Locked manual values survive unless the administrator accepts the Excel value.
- Products missing from a file remain in the catalog.
- Ambiguous images are retained for review and are not published as confirmed photos.
- A public response cannot contain discount notes, source-column labels, server paths, or import diagnostics.
- Russian, Uzbek, and English routes render localized interface text. Untranslated product copy is labeled as the Russian original.
