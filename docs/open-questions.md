# Open questions

Confirmed decisions are not listed here. In particular, the company name is HikVision, numeric prices are stored as USD and displayed as UZS from the source workbook, blank prices initialize to the public request-price state, the site is Russian, Uzbek, and English, stock is an out-of-stock badge set by staff, and the two workbooks import independently or together.

## Client decisions still open

1. **Domain.** The client already owns a domain. The exact host was not provided. Canonicals, the sitemap, and HTTPS use `PUBLIC_SITE_URL` until it is supplied. No domain will be invented.
2. **Contact details and social links.** Phone, email, address, opening hours, and social URLs are empty profile fields. The admin can save them. The public page shows only saved values. Organization address and telephone stay out of structured data until then.
3. **Tax wording.** Visitors see the calculated UZS amount. The client has not said whether the page should also say that tax is included or excluded. The stored USD amount and the display formula do not change either way.

## Technical decisions already made

These do not need a client answer unless they should change.

- Modular monolith: Next.js, FastAPI, PostgreSQL, Nginx, Docker on one VPS. No Redis, Celery, or microservices.
- Default locale and `x-default` are Russian, because that is the workbook language.
- Uzbek interface copy uses Latin script.
- The same product slug is used under `/ru`, `/uz`, and `/en`.
- Missing Uzbek or English product text shows the Russian original with a translated caption. It is not stored as a translation.
- A blank price cell remains `blank` on the source record and starts as public `on_request`. It is never zero.
- Hilook `F103`, `F106`, `F107`, and `F115` stay internal. Public amounts are the `Цена` values 115, 115, 200, and 200 USD.
- Unverified brands stay null and are flagged. The company name is not used as a guessed manufacturer.
- One administrator role.
- Local checksum media, with `storage_backend` ready for object storage later.
- New products start in stock. Import never sets out of stock.
- A product missing from a file is reported and kept until an administrator archives it.

## Not questions

The following are already specified in `docs/project-requirements.md`: company name, USD storage with workbook-based UZS display, EZVIZ `Цена для дилера` as the initial stored price, one public price without a discount badge, request-price labels in three languages, the browser product list, separate records for repeated models, workbook images, three-language routes, out-of-stock display, and the two-workbook import with one apply step.
