# Database design

PostgreSQL schema for the HikVision catalog. Identifiers are `bigint generated always as identity` unless noted. Timestamps are `timestamptz`. Status fields are `text` with `CHECK` constraints.

Money is `numeric(12,2)`. Floating-point types are not used for prices. Source amounts in the current files run from 0.1 to 2200 and include fractional values.

Image and workbook bytes are not columns on product rows.

## Visibility

- **Public** fields may appear in the public API and HTML.
- **Admin** fields appear only on authenticated admin routes.
- **Internal** fields are admin-only and must never be copied into a public serializer. This includes the EZVIZ column name `Цена для дилера`, Hilook discount notes, raw import payloads, password hashes, session hashes, and absolute filesystem paths.

## How the hard rules are represented

- **Repeated models** are separate `products` rows. There is no unique constraint on the model. Each row has its own id and slug. A `product_source_records` row points at that id. Matching uses the source identity, not the model alone.
- **One workbook at a time.** `product_source_records.source_code` is `hikvision` or `ezviz`. An apply updates only rows whose source code is in the job. The other code is not selected.
- **Combined jobs.** `import_jobs` is the unit the administrator approves. `import_files` holds one row per uploaded workbook, so history still shows which file was which.
- **Manual edits.** Lock columns on `products` and on translation rows. Apply changes a locked field only when that row’s resolution is `accept_excel`.
- **Missing products.** They stay. The source row is flagged `absent_from_latest` for the source that was actually uploaded. `catalog_status` changes only when an administrator archives or unpublishes.
- **Translations.** Russian source text is stored as locale `ru`. Uzbek and English are separate rows and start empty. Fallback is a read-time flag, not a copied fake translation.
- **Prices.** The source snapshot keeps blank, explicit `По запросу`, and numeric apart. The public status initialized from a blank cell is `on_request`, with a null amount. Numeric public prices use currency `USD`.
- **Images.** Many `product_images` rows per product. Link confidence is a status. Unassigned files remain on `import_assets`.
- **Recovery.** Live catalog writes for one apply commit in one database transaction. Files are checksum objects written before commit. A rolled-back transaction does not remove objects that existing rows still reference. Re-applying the same job is rejected by status.

## Brands

`brands`

| Column | Type | Null | Visibility | Notes |
| --- | --- | --- | --- | --- |
| id | bigint | no | admin | Primary key |
| slug | text | no | public | Unique, language-neutral |
| is_published | boolean | no | public filter | |
| created_at, updated_at | timestamptz | no | admin | |

`brand_translations`

| Column | Type | Null | Visibility | Notes |
| --- | --- | --- | --- | --- |
| brand_id | bigint | no | public via parent | FK `ON DELETE CASCADE` |
| locale | text | no | public | `ru`, `uz`, or `en` |
| name | text | no | public | |
| description | text | yes | public | |
| seo_title, seo_description | text | yes | public | |

- Primary key: `(brand_id, locale)`.
- Delete brand: `RESTRICT` while products reference it.
- A brand is created only from verified evidence or from an administrator. Unclear rows leave `products.brand_id` null and are flagged. They are not given the company name as a manufacturer.

Verified proposals from the current files: `EZVIZ` for the EZVIZ workbook; `HiLook` for the Hilook sheet when the row is a HiLook model; `Hikvision` when the model or description identifies that manufacturer; `WD`, `Seagate`, `Andel`, and `Cougar` when the model or description names them. Generic accessories with no manufacturer stay unbranded until review.

## Categories

`categories`

| Column | Type | Null | Visibility | Notes |
| --- | --- | --- | --- | --- |
| id | bigint | no | admin | |
| parent_id | bigint | yes | public | Self FK, `ON DELETE RESTRICT` |
| slug | text | no | public | Unique among siblings |
| source_code | text | yes | admin | `hikvision` or `ezviz` when the category was proposed from a file |
| source_worksheet | text | yes | admin | Provenance, not a frozen public name |
| source_heading | text | yes | admin | Hilook label, when used |
| sort_order | integer | no | public | |
| is_published | boolean | no | public filter | |
| created_at, updated_at | timestamptz | no | admin | |

`category_translations` mirrors brand translations: `(category_id, locale)` primary key, `name`, optional `description`, `seo_title`, `seo_description`.

- Unique: `(COALESCE(parent_id, 0), slug)`.
- Delete: `RESTRICT` when products or children exist.
- Worksheet names and Hilook headings seed the Russian name. Administrators can rename and translate without changing provenance columns.
- Headings with no direct products, such as Hilook `NVR` or `DVR`, are still category proposals.

## Products

`products`

| Column | Type | Null | Visibility | Notes |
| --- | --- | --- | --- | --- |
| id | bigint | no | admin | Stable id. Not used in the public URL |
| brand_id | bigint | yes | public | FK `ON DELETE RESTRICT`. Null when the brand is unverified |
| category_id | bigint | yes | public | FK `ON DELETE RESTRICT` |
| product_kind | text | no | public | `product` or `service` |
| model_raw | text | no | admin | Exact source text when imported |
| model_display | text | no | public | Trimmed, whitespace collapsed. Shared across locales unless a translation overrides the visible name |
| model_normalized | text | no | admin | Match and warning key. Not unique |
| option_label | text | yes | public | EZVIZ `Доп-опция` |
| public_price_status | text | no | public | `numeric`, `on_request`, or `hidden` |
| public_price_amount | numeric(12,2) | yes | public, with rules | |
| public_currency | char(3) | yes | public | `USD` when status is `numeric`. Otherwise null |
| price_locked | boolean | no | admin | True after an admin price edit |
| option_locked | boolean | no | admin | |
| brand_locked | boolean | no | admin | |
| category_locked | boolean | no | admin | |
| model_locked | boolean | no | admin | True after an admin edit of `model_display` |
| stock_status | text | no | public | `in_stock` or `out_of_stock`. Default `in_stock`. Not imported from Excel |
| slug | text | no | public | Unique. Language-neutral. Same path segment in every locale |
| catalog_status | text | no | public filter | `draft`, `published`, or `archived` |
| deleted_at | timestamptz | yes | admin | Soft delete. Public queries require null |
| created_at, updated_at | timestamptz | no | admin | |
| price_updated_at | timestamptz | yes | admin | |

There is **no** unique constraint on `model_normalized` or on `(brand_id, model_normalized)`.

Indexes: unique `slug`; b-tree on `brand_id`, `category_id`, `(catalog_status, deleted_at)`, `model_normalized`.

`product_kind = service` is for the four EZVIZ cloud-history rows. They remain sellable catalog entries.

`stock_status` does not affect `public_price_status`. Excel has no stock column, so import does not write this field.

`hidden` is an administrator override. Import never sets it. The public serializer omits the amount.

### Price check

```text
CHECK (
  (public_price_status = 'numeric'
    AND public_price_amount IS NOT NULL
    AND public_price_amount >= 0
    AND public_currency = 'USD')
  OR (public_price_status = 'on_request'
    AND public_price_amount IS NULL
    AND public_currency IS NULL)
  OR (public_price_status = 'hidden'
    AND public_currency IS NULL
    AND (public_price_amount IS NULL OR public_price_amount >= 0))
)
CHECK (stock_status IN ('in_stock', 'out_of_stock'))
CHECK (catalog_status IN ('draft', 'published', 'archived'))
CHECK (product_kind IN ('product', 'service'))
```

| Public status | Amount | What visitors see |
| --- | --- | --- |
| `numeric` | required USD | `$` and the amount. One price. No discount |
| `on_request` | null | Locale request-price label |
| `hidden` | omitted publicly | No price |

Zero is a numeric amount only if a future file actually contains zero. A blank cell is not stored as zero. On first import a blank cell still becomes public `on_request`.

### Source price versus public price

`product_source_records` holds the workbook value. `products` holds the editable public value.

| Source cell | `source_price_kind` | Initial public status |
| --- | --- | --- |
| Number in `Цена` or EZVIZ `Цена для дилера` | `numeric` | `numeric`, same amount, `USD` |
| Text that trims to `по запросу` | `explicit_on_request` | `on_request` |
| Empty price cell | `blank` | `on_request`, amount null |
| Hilook column F note | not a price | ignored for the public amount. Stored in `internal_note` |

The first apply copies the initial public status and leaves price locks false. An administrator edit sets `price_locked`. Later applies refresh the source columns always, and change the public price only when the row resolution is `accept_excel` or the field is unlocked. The batch flag `replace_prices` sets the default resolution of price conflicts to `accept_excel` and the preview lists those rows before apply.

No price-history table. Audit is the source snapshot, the import report, and an audit-log entry when an administrator changes a price.

## Product translations

`product_translations`

| Column | Type | Null | Visibility | Notes |
| --- | --- | --- | --- | --- |
| product_id | bigint | no | public via parent | FK `ON DELETE CASCADE` |
| locale | text | no | public | `ru`, `uz`, `en` |
| localized_name | text | yes | public | Optional override. Empty means show `model_display` |
| description | text | yes | public | |
| seo_title, seo_description | text | yes | public | |
| description_locked | boolean | no | admin | |
| origin | text | no | admin | `source`, `manual`, or `empty` |
| search_vector | tsvector | yes | internal | `russian` for `ru`, `english` for `en`, `simple` for `uz` |

- Primary key: `(product_id, locale)`.
- The Excel description is inserted as `locale = ru`, `origin = source`.
- Uzbek and English rows are not filled with Russian text. A missing description has `origin = empty` or no row. The API fallback flag tells the page to show the Russian description with a translated caption such as “Original description (Russian)”.
- Import updates the Russian description only when `description_locked` is false or the resolution is `accept_excel`. It never writes `uz` or `en` from the workbook, because the workbook is not a translation.

## Specifications

`product_specifications`

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| id | bigint | no | |
| product_id | bigint | no | FK `ON DELETE CASCADE` |
| sort_order | integer | no | |

`product_specification_translations`

| Column | Type | Null | Visibility |
| --- | --- | --- | --- |
| specification_id | bigint | no | public via parent |
| locale | text | no | |
| name, value | text | no | public |

- Primary key: `(specification_id, locale)`.
- The initial import creates no specification rows. The Russian description remains the authoritative prose.
- Only `origin` is not needed here: a specification is public in a locale only when that locale’s translation row exists. An optional extractor, if added later, must store suggestions outside the public table until an administrator approves them. It is not part of the first import.

## Source records

`product_source_records` — one current mapping per imported product.

| Column | Type | Null | Visibility | Notes |
| --- | --- | --- | --- | --- |
| id | bigint | no | admin | Durable source identity |
| product_id | bigint | no | admin | FK `ON DELETE CASCADE` |
| source_code | text | no | admin | `hikvision` or `ezviz` |
| source_workbook | text | no | admin | Original filename of the last apply |
| source_worksheet | text | no | admin | |
| source_row | integer | no | admin | Last seen 1-based row. Not the match key |
| source_line_number | text | yes | admin | `№` cell. Not unique |
| source_model_raw | text | no | admin | |
| source_option_raw | text | yes | admin | |
| source_description_raw | text | yes | admin | |
| source_description_sha256 | char(64) | yes | admin | |
| source_price_header | text | yes | internal | `Цена для дилера` or `Цена` |
| source_price_raw | text | yes | internal | |
| source_price_kind | text | no | internal | `numeric`, `explicit_on_request`, or `blank` |
| source_price_amount | numeric(12,2) | yes | internal | |
| section_label, parent_section_label | text | yes | admin | Hilook headings |
| internal_note | text | yes | internal | Hilook column F only |
| match_key | text | no | admin | `source_code + worksheet + model_normalized + option + description hash` |
| first_job_id, last_job_id | bigint | no | admin | FK `ON DELETE RESTRICT` |
| last_seen_at | timestamptz | no | admin | |
| absent_from_latest | boolean | no | admin | For this source code only |

- Unique: `match_key`.
- Unique: `product_id` for imported products (one source mapping each).
- Index: `(source_code, source_worksheet)`, `(absent_from_latest)`.
- Two products with the same model and different descriptions or options have different keys and different ids.
- If an incoming key matches two live rows, the import row is a conflict and nothing is written.
- A manually created product has no source record. Imports do not mark it absent and do not attach it by model name.

## Images

`product_images`

| Column | Type | Null | Visibility | Notes |
| --- | --- | --- | --- | --- |
| id | bigint | no | admin | |
| product_id | bigint | no | public via parent | FK `ON DELETE CASCADE` |
| storage_backend | text | no | admin | `local` or later `s3` |
| object_key | text | no | admin | Relative key, not an absolute path |
| mime_type | text | no | admin | png, jpeg, or webp |
| byte_size | integer | no | admin | |
| sha256 | char(64) | no | admin | |
| width, height | integer | yes | admin | |
| sort_order | integer | no | public | |
| is_primary | boolean | no | public | Partial unique: one primary per product among non-rejected rows |
| alt_text | text | yes | public | Default `{brand} {model}`, or `{model}` when the brand is null. The company name is not used as a substitute brand. One default is enough at launch because the model code is language-neutral; an administrator can edit it |
| association_status | text | no | admin | `high`, `needs_review`, `confirmed`, `rejected` |
| source_code, source_worksheet | text | yes | admin | |
| anchor_row, anchor_col, anchor_to_row | integer | yes | admin | |

Public API returns an image only when status is `high` or `confirmed`, the product is published, and it is not archived. `needs_review` and `rejected` stay in admin.

Deleting image rows does not delete a checksum object that another row still uses.

## Slug redirects

`slug_redirects`

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| id | bigint | no | |
| from_slug | text | no | Unique |
| product_id | bigint | no | FK `ON DELETE CASCADE` |
| created_at | timestamptz | no | |

Public locale paths 301 `/{locale}/products/{from_slug}` to the current slug. Import does not change an existing slug.

## Admin identity

`admin_users`: `id`, unique `email`, `password_hash` (Argon2id, internal), `role` checked as `admin`, `is_active`, `last_login_at`, timestamps.

`admin_sessions`: `id uuid`, `user_id` FK cascade, `token_hash` internal, `expires_at`, `revoked_at`, `created_at`. Index on `token_hash`.

One role is enough for launch. The column exists so a later role does not require a new table.

## Import jobs

`import_jobs` — one approval unit, containing one or both sources.

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| id | bigint | no | |
| status | text | no | `preview`, `rejected`, `applying`, `applied`, `failed` |
| created_by | bigint | no | FK `admin_users` |
| approved_by | bigint | yes | Set when apply starts |
| replace_prices | boolean | no | Default false |
| summary | jsonb | yes | Counts |
| error_message | text | yes | |
| created_at, applied_at | timestamptz | | |

Apply is allowed only from `preview`. The handler sets `applying` in the same transaction as the catalog writes, then `applied`. A retry after `applied` does nothing and returns the existing result. A retry after `failed` requires a new job, not a second commit of a half-applied one. Because the catalog writes commit only at the end, a failed job has not changed live rows.

`import_files`

| Column | Type | Null | Notes |
| --- | --- | --- | --- |
| id | bigint | no | |
| job_id | bigint | no | FK cascade |
| source_code | text | no | `hikvision` or `ezviz` |
| original_filename | text | no | |
| sha256 | char(64) | no | |
| identification | text | no | `auto` or `admin_confirmed` |
| validation_status | text | no | `valid` or `invalid` |
| validation_errors | jsonb | no | |
| stored_object_key | text | no | Internal copy |
| included_in_apply | boolean | no | False when invalid or removed from the job |

- Unique: `(job_id, source_code)`.
- A job cannot contain two files of the same source.

`import_rows` belong to `import_file_id`.

| Column | Type | Notes |
| --- | --- | --- |
| id, import_file_id, worksheet_name, source_row | | |
| classification | | `product`, `service`, `heading`, `blank`, `stray`, `invalid` |
| action | | `insert`, `update`, `unchanged`, `possible_match`, `conflict`, `exclude`, `skip` |
| resolution | | `pending`, `keep_current`, `accept_excel`, `accept_new` |
| raw_cells | jsonb internal | Includes unlabeled notes |
| proposal | jsonb admin | |
| matched_product_id | bigint null | |
| messages | jsonb | |
| applied | boolean | |

`possible_match` and unresolved `conflict` rows are excluded from apply until the administrator sets a resolution. They do not block the rest of the job.

`import_assets` — every extracted image, including unassigned ones.

| Column | Notes |
| --- | --- |
| import_file_id, object_key, sha256, mime_type | |
| worksheet, anchor_row, anchor_col, anchor_to_row | |
| proposed_product_id | null when unassigned |
| link_status | `linked_high`, `linked_review`, `unassigned`, `shared_candidate` |

Unassigned and shared-candidate assets are not dropped and are not copied onto extra products.

## Company profile

`business_profile` is a single row (`id = 1`).

| Column | Visibility | Notes |
| --- | --- | --- |
| public_name | public | Default `HikVision` |
| legal_name | public when set | |
| domain | public when set | Empty until provided. No invented host |
| phone, email, address, opening_hours | public when set | Placeholders are empty, not fake numbers |
| social_links | public when set | JSON array of `{network, url}` edited in admin |
| logo_object_key | admin | |
| updated_at | admin | |

The contact page and Organization structured data include only fields that are non-empty.

## Audit log

`admin_audit_log`

| Column | Type | Notes |
| --- | --- | --- |
| id | bigint | |
| actor_id | bigint | FK `admin_users` `ON DELETE RESTRICT` |
| action | text | For example `login`, `price_change`, `catalog_status`, `profile_update`, `import_apply` |
| entity_type, entity_id | text, bigint null | |
| detail | jsonb | Before/after summary. No passwords, session tokens, or full workbook dumps |
| ip_address | text | |
| created_at | timestamptz | |

Append-only from the application. Admin can read it. Public routes cannot.

## Relationships

```text
brands 1—* products
brands 1—* brand_translations
categories 1—* categories
categories 1—* products
categories 1—* category_translations
products 1—* product_translations
products 1—* product_specifications 1—* product_specification_translations
products 1—* product_source_records
products 1—* product_images
products 1—* slug_redirects
admin_users 1—* admin_sessions
admin_users 1—* import_jobs
admin_users 1—* admin_audit_log
import_jobs 1—* import_files 1—* import_rows
import_files 1—* import_assets
```

## Why this is enough

The live catalog, the per-source mapping, and the job/file split answer the two-workbook workflow without a second database. Translation rows keep Russian source text intact. Price kind on the source row preserves blank versus explicit `По запросу` after the public status has been initialized to the request-price label. Discount notes never have a public column.
