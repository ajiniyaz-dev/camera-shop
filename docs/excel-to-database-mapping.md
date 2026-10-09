# Excel to database mapping

Worksheet names are provenance. They seed a Russian category name only where this document says so. An administrator can rename and translate that category without changing source columns.

Visibility matches `docs/database-design.md`. “Seed” means the first apply copies the value into the live column. Later applies follow the lock and resolution rules in `docs/import-strategy.md`.

Both files are mapped independently. A Hikvision upload does not write EZVIZ columns, and the reverse is also true.

## Identity

| Workbook | Worksheet | Source | Database | Visibility | Transformation | Validation | Import / update |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Both | All | File signature | `product_source_records.source_code` | admin | `hikvision` or `ezviz` | Required. Never inferred from a neighboring product | Set on insert. Not changed by the other file |
| Both | All | Filename | `import_files.original_filename` and `source_workbook` | admin | Stored as uploaded | Supporting evidence only | Refreshed on the source record when that source is applied |
| Both | All | Worksheet name | `source_worksheet` | admin | Unchanged | Required | Refreshed for this source |
| Both | All | Row index | `source_row` | admin | 1-based | Not a permanent id | Refreshed after a confident match. Not used alone to find a product |
| Both | All | Derived | `match_key` | admin | Source code, worksheet, normalized model, normalized option, description SHA-256 | Unique | Exact key updates one product. Two live rows with the incoming key conflict. No merge |
| Both | All | Derived | `products.id` | admin | New id per inserted product | | Never reused to collapse two source rows |
| Both | All | Derived | `products.slug` | public | Once, from brand (or `product` if the brand is null), model, and option. Suffix if needed | Unique across products | Create on insert. Later imports do not change it |

## Shared columns

| Workbook | Worksheet | Source column | Database | Visibility | Transformation | Validation | Import / update |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Both | All | `№` | `source_line_number` | admin | Raw text | Duplicates and restarts allowed | Refresh source. Not public |
| Both | All | `Фото` cell | — | — | The cell is empty. Ignore it as a value | | Images come from anchors |
| Both | All | `Модель` | `model_raw`, `source_model_raw` | admin | Exact text | Required for a product or service | Source copy refreshes on match. `model_raw` on the product is set on insert |
| Both | All | `Модель` | `model_display` | public | Trim and collapse whitespace | Non-empty | Set on insert. Later imports change it only when `model_locked` is false or the resolution is `accept_excel` |
| Both | All | `Модель` | `model_normalized` | admin | Case-fold. Dash-fold only inside the key | Not unique | Used for warnings and the match key |
| Both | All | `Характеристика` | `product_translations` (`ru`, `description`) | public | Trim ends only. Keep internal text | Empty becomes null | Seed Russian. Keep when `description_locked` unless resolution is `accept_excel`. Do not copy into `uz` or `en` |
| Both | All | `Характеристика` | `source_description_raw`, `source_description_sha256` | admin | Hash the trimmed description or an empty string | | Always refresh on match for this source |
| EZVIZ | Ezviz | `Доп-опция` | `option_label` | public | Trim. Keep source spelling, including `с солнечной панель` and the colons on the billing options | Optional | Seed. Respect `option_locked` |
| Hikvision | All sheets | — | `option_label` | public | No column. Leave null | | Do not invent an option |
| Both | All | Row class | `product_kind` | public | `service` for the four EZVIZ cloud-history rows; otherwise `product` | | Set on insert. Import does not flip it later |
| Both | All | — | `stock_status` | public | Not in Excel | | New rows start `in_stock`. Import never changes stock |

## Prices

| Workbook | Worksheet | Source column | Database | Visibility | Transformation | Validation | Import / update |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EZVIZ | Ezviz | `Цена для дилера` | `source_price_header`, `source_price_kind`, `source_price_amount` | internal | Header stored as `Цена для дилера`. Number becomes kind `numeric` and `numeric(12,2)` | Current file: 84 numbers, including 92.5. Other text is invalid and the row is held | Refresh source on EZVIZ apply only |
| EZVIZ | Ezviz | `Цена для дилера` | `public_price_status`, `public_price_amount`, `public_currency` | public | Initial public price. `numeric`, same amount, currency `USD`. Display with `$` | Amount `>= 0`. Not a float column | Seed. Later: change only when unlocked or resolution is `accept_excel`. Never label it as a dealer price on the site |
| Hikvision | All 11 sheets | `Цена` | source price columns, header `Цена` | internal | Number → `numeric`. Trimmed `по запросу` → `explicit_on_request`. Empty → `blank` | The only non-numeric price text in the current file is ` По запросу ` (42 cells). Unexpected text is invalid | Refresh source on Hikvision apply only |
| Hikvision | All 11 sheets | `Цена` | public price columns | public | Numeric → `numeric` USD. Explicit `По запросу` → `on_request`. **Blank → public `on_request` with null amount.** Source kind stays `blank` | Blank is not 0 and not a fabricated number | Seed, then respect the price lock unless the administrator accepts Excel or turns on `replace_prices` |
| Hikvision | Hilook | Column F, no header | `internal_note` | internal | Raw note | Verified values: `F103` and `F106` = `текущая цена со скидкой 60$`; `F107` and `F115` = `текущая цена со скидкой 100$`. Main prices remain `E103` 115, `E106` 115, `E107` 200, `E115` 200 | Never copied into `public_price_amount`. Never returned by a public API |

`hidden` is not mapped from Excel.

## Categories and brands

| Workbook | Worksheet | Source | Database | Visibility | Transformation | Validation | Import / update |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EZVIZ | Ezviz | Sheet name | Russian category name `Ezviz` | public after translation | One category. No in-sheet headings | Admin may rename and add `uz` / `en` | Seed `category_id` unless `category_locked` and resolution is keep |
| Hikvision | Sheets other than Hilook’s heading rule | Sheet name | Russian category name from the sheet (`IP камеры`, `NVR`, `PTZ`, `Проектное оборудование`, `Домофоны`, `СКУД`, `Коммутаторы`, `HDD`, `Звуковое оборудование`, `другие устройства`) | public name | Store the sheet on `source_worksheet` | Stray numbers do not create categories | Same lock rule. Only when this source is in the job |
| Hikvision | Hilook | Column A label | Category proposal plus `section_label` and `parent_section_label` | category public; provenance admin | One-cell text label. Zero-product labels `Turbo HD камера`, `NVR`, `DVR`, and `PTZ` are proposed parents | Preview shows the tree. Labels are not products | Reuse a category with the same source sheet and heading |
| EZVIZ | Ezviz | Workbook | `brand_id` → EZVIZ | public | The file is that brand’s list | | Respect `brand_locked` |
| Hikvision | Hilook and other sheets | Model and description text | `brand_id` | public | Set HiLook, Hikvision, WD, Seagate, Andel, or Cougar only when the text identifies that brand. Otherwise leave null and flag the row | Do not assign the company name to fill a gap | Respect `brand_locked`. A null brand does not block insert |

## Images

| Workbook | Worksheet | Source | Database | Visibility | Transformation | Validation | Import / update |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Both | All | Anchor on a model row, column B | `product_images.association_status = high` | public when the product is published | Extract to the checksum store. Record anchors | PNG, JPEG, or WebP by content | On a later apply of this source, add a checksum the product does not have. Do not delete existing images. Do not change an administrator-chosen primary |
| Both | All | Anchor on a model row, other column | `needs_review` | admin until confirmed | Same extract | Same MIME rule | Stays non-public |
| Both | All | Anchor not on a model row | `import_assets.link_status = unassigned` | admin | Keep the file and the anchor | | Never auto-link |
| Both | All | Merged photo range covering extra model rows | `shared_candidate` | admin | Report only | | Link only after confirmation |
| Both | All | Derived | `alt_text` | public | `{brand} {model}` or `{model}` when the brand is null | | Do not overwrite admin alt text |

## Rows that do not become products

| Source | Database | Behavior |
| --- | --- | --- |
| Empty row | `import_rows.classification = blank` | Count and skip. EZVIZ has a long empty used range |
| Hilook section label | `heading` and a category proposal | Not a product |
| `IP камеры` values `1` and `11`, `HDD` value `17` | `stray` | Not a product and not a category |
| Header row | Column map only | A missing required header fails that sheet |

## Fields the importer does not fill

| Column | Reason |
| --- | --- |
| `uz` and `en` translations | The workbook is Russian. Invented translations are not allowed |
| Specification tables | Descriptions are prose |
| SEO overrides | Admin-owned. Templates generate them when null |
| `stock_status` | Not in the files. Default `in_stock` on insert only |
| `public_price_status = hidden` | Admin only |
| `catalog_status = archived` | Admin only. Absence from a file sets `absent_from_latest` on that source |
| Passwords and sessions | Unrelated |

## Examples

- EZVIZ `CS-DP2C` amount `92.5` → public `92.50` USD from `Цена для дилера`.
- A project-equipment cell ` По запросу ` → source `explicit_on_request`, public `on_request`.
- An HDD row with an empty `Цена` → source `blank`, public `on_request`, amount null. The product is inserted.
- Hilook `E103` 115 and `F103` discount note → public 115 USD, note internal.
- EZVIZ rows 83 and 85 share a model and differ in `Доп-опция` → two service products and two slugs.
- Two `BNC` rows with different descriptions → two products.
- A second upload of the same EZVIZ file does not insert those rows again and does not touch Hikvision products.
