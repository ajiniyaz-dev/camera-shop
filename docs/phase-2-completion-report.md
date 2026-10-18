# Phase 2 — presentation completion

18 October 2026. The core Phase 2 presentation is implemented and the local Docker site at `http://127.0.0.1:8080` has been verified, including a final regression on that same site. The `api` and `web` images were rebuilt and those two containers were recreated. Postgres and nginx were left running. Volumes, catalog rows, and media files were not changed.

No catalog row was edited. Published products remain 639. Product 56 still has no image association. The workbooks were not saved. No import or migration ran. Nothing was committed, pushed, or deployed.

## What changed

### Titles

A model code such as `IPC-D160HA-LU` or `BNC` is shown as the title without a note that it is a Russian original. The public API treats a non-Cyrillic fallback title the same way. A Russian sentence used as the title, including the four video-history plan names, still shows a short label: Russian `На русском языке`, Uzbek `Rus tilida`, English `In Russian`. Descriptions that fall back to Russian keep that label. No translated titles were generated. URLs, slugs, and SEO titles were not rewritten.

### Services

Products 638–641 are marked `Услуга` / `Xizmat` / `Service`. The stored option `Ежемесячно:` or `Ежегодно:` is shown as monthly or yearly billing in the page language. The 7-day and 30-day names, the existing descriptions, and the prices 3, 5, 30, and 50 USD stay as they are. Other option text, including `с солнечной панель`, is still shown as stored.

The public product payload includes `product_kind`. The rebuilt API returns `service` for products 638–641. The pages also recognize the two billing phrases if that field is absent.

### Navigation and labels

Brand and category are separate labeled links. `EZVIZ` as a brand goes to `/brands/ezviz`. `EZVIZ` as a category goes to `/categories/ezviz`. A product with only one of them shows only that link.

A published brand with no published products is left out of the brand list, brand filter, brand page, and sitemap. The brand row is not deleted and its products are not reassigned. Seagate was checked again: it has five published products, so it remains visible. The same is true of WD, Andel, and Cougar. The unpublished `other` brand was already hidden.

Homepage category cards, the “other sections” chips, and the category directory no longer print product counts. A search or an active price, brand, or category filter still shows `Результаты` / `Natijalar` / `Results` with the match count. A plain category or catalog page does not.

The homepage introduction describes a catalog of video-surveillance equipment, security equipment, and related services, and says the site does not take orders or payments. The same sentence is in the footer on every page. Wording that talked about publication state was replaced with visitor-facing section and product labels.

### Selection

`/ru/selection`, `/uz/selection`, and `/en/selection` hold a temporary list in `localStorage`. Visitors can add a product, open the list, and remove an item. A second add keeps one entry. The header count follows the list. Each entry shows the current name, model, billing period when it applies, and the current price. The page says the list stays in this browser and is not an order or a payment. There is no checkout, reserve, email, or share action. The list holds at most 50 products. A slug that returns 404 is removed and a short note says it left the catalog. A failed request leaves that entry in place and says part of the list could not be loaded. The page is `noindex` and is not in the sitemap.

### Images

`ProductPhoto` is unchanged from the previous batch. On `http://127.0.0.1:8080`, the BNC page HTML uses `w-auto`, `object-contain`, and `max-h-[32rem]`. The 105×60 BNC photo stays 105×60 on a 1920px desktop and on a 390px width, with `object-fit: contain`. The CS-H1C photo is 3508×2480 and is shown at 592×419 on the 1920px desktop, so the large file is scaled down and the aspect ratio is kept. Product 56 shows `Нет изображения`, `Rasm yo'q`, and `No image`, with no `<img>` on any of the three pages. It still has no `product_images` row.

On `http://127.0.0.1:8080`, the `IPC-B469HAD-LUF/SL` gallery starts on the 335×142 photo at its own pixel size. Choosing the second thumbnail switches the main image to the 493×222 photo, also at its own pixel size and with `object-fit: contain`. Choosing the first thumbnail switches back. The thumbnails are smaller than the files. The 325×230 mobile measurement of CS-H1C remains the earlier check on the port 3012 dev server.

## Files

Public API and its test:

- `api/app/public/router.py`
- `api/tests/test_public_catalog.py`

Website:

- `web/src/lib/public-i18n.ts`
- `web/src/lib/public-api.ts`
- `web/src/lib/presentation.ts`
- `web/src/lib/presentation.test.mts`
- `web/src/lib/selection.ts`
- `web/src/lib/selection.test.mts`
- `web/src/components/public/catalog-links.tsx`
- `web/src/components/public/selection-button.tsx`
- `web/src/components/public/selection-link.tsx`
- `web/src/components/public/selection-view.tsx`
- `web/src/components/public/product-card.tsx`
- `web/src/components/public/home-cards.tsx`
- `web/src/components/public/product-listing.tsx`
- `web/src/components/public/category-view.tsx`
- `web/src/components/public/site-header.tsx`
- `web/src/components/public/site-footer.tsx`
- `web/src/app/[locale]/page.tsx`
- `web/src/app/[locale]/products/[slug]/page.tsx`
- `web/src/app/[locale]/categories/page.tsx`
- `web/src/app/[locale]/brands/[slug]/page.tsx`
- `web/src/app/[locale]/selection/page.tsx`

Docs:

- `docs/phase-2-completion-report.md`
- `docs/PROJECT_HANDOFF.md`

## Checks

Against `http://127.0.0.1:8080` after the rebuild:

- `GET /api/health` returned `{"status":"ok","database":"ok"}`. All four containers were healthy. Postgres and nginx had been up for about six hours; only `api` and `web` were recreated.
- Published products: 639. Product 56 has zero image rows.
- `/ru/selection`, `/uz/selection`, and `/en/selection` load, including the empty state and the note that the list is not an order or a payment.
- Adding BNC set the header count to 1 and changed the button to remove. Reloading kept that one entry. The selection page showed the name, model, and `$0.15`. Removing it returned the count to 0 and the empty state.
- Products 638 and 641 were opened in English and show `Service`, `In Russian`, and `Billing: Monthly` at `$3.00` or `Billing: Yearly` at `$50.00`. The other two English pages contain `Service` with `Monthly` or `Yearly`. The API returns `product_kind=service` for all four, with prices 3, 5, 30, and 50 USD and the stored monthly or yearly option.
- On the 7-day plan, `Brand: EZVIZ` goes to `/en/brands/ezviz` and `Category: EZVIZ` goes to `/en/categories/ezviz`.
- The public brand list is Andel, Cougar, EZVIZ, Hikvision, HiLook, Seagate, and WD. `GET /api/public/brands/other` is not found. There is no published brand with zero published products in this database, so that live case is not present. The isolated API test covers a spare brand with no products.
- BNC and CS-H1C image sizes, and the product 56 placeholders, as in the Images section.

Final regression on `http://127.0.0.1:8080`, 18 October 2026:

- `GET /api/health` returned `{"status":"ok","database":"ok"}`. Published products: 639.
- `IPC-B469HAD-LUF/SL` gallery switches between the 335×142 and 493×222 photos, as in the Images section.
- Selection in Russian, Uzbek, and English: add sets the count to 1 and changes the button to remove; a stored duplicate still displays as one item; leaving the page and coming back keeps the item; refresh keeps it; remove returns the empty state. The test selection was cleared afterward.
- Product 56 has no image and shows `Нет изображения`, `Rasm yo'q`, and `No image`, without a Russian-original note on the model code.
- Products 638–641 are services. English pages show Monthly or Yearly. The Russian pages show `Услуга` with `Ежемесячно` or `Ежегодно`. The Uzbek pages show `Xizmat` with `Oylik` or `Yillik`. API prices remain 3, 5, 30, and 50 USD.

Earlier, on the dev server at port 3012, before the image rebuild: homepage introduction and category cards, search for `BNC` with a result count, Seagate still listed, and a missing selection slug.

Automated tests, not pointed at the Compose catalog:

- `npm run typecheck` passed.
- Frontend presentation, selection, photo, and homepage tests: 22 passed.
- `tests/test_public_catalog.py`: 7 passed on a disposable Postgres container that shared no network with Compose. That container and its network were removed. The Compose catalog was not used.

## Left unchanged on purpose

- No workbook drawing was attached or removed. The image audit’s rejected and unverified files stay off the products.
- Product 56 has no replacement photo.
- English and Uzbek service titles were not invented. The existing descriptions carry the translated plan text.
- Seagate’s products and brand assignment were not changed.
- The solar-panel option text was not translated.
- No inquiry, email, or messenger action was added.
- Prices, descriptions, translations, categories, slugs, images, source records, and publication status were not edited.

## Deferred

The core Phase 2 implementation and the local Docker verification are complete. These items stay open on purpose:

- Product 56 still has no genuine camera photo. The public page shows the no-image placeholder.
- Rejected and unverified workbook drawings stay unattached.
- A send or share action for the selection is optional and needs a separate decision.
- Phase 8 deployment, the real domain, and contact details remain open. Do not invent them.

The Compose site is port 8080. On 18 October, `/uz/catalog` and `/uz/categories` rendered there with the catalog and category lists, and `/admin/profile` redirected to the login form. No static asset on those pages returned an error.

Port 3010 is a separate `npm run start` process. It is not the Compose site. Its production `.next` output was later replaced by the dev server on port 3012, which uses the same directory. The preview still serves its old HTML, but every `/_next/static` file that HTML references returns 400, so the browser shows a client-side exception. Do not run `next dev` and `next start` against one `.next` directory. Restoring port 3010 needs a new production build while the dev server is not writing that directory, then a restart of that preview only.
