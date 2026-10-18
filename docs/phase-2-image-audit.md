# Phase 2 — Product image presentation audit

18 October 2026. Read-only inventory of the 639 published products. The inventory itself changed no catalog row, image association, workbook, price, or description, and applied no import. The two corrections approved from this audit are recorded in [First approved batch](#first-approved-batch--completed).

The comparison used the live catalog and the original `data/source/Hikvision pr.xlsx` and `data/source/Ezviz pr.xlsx`. Workbooks were parsed in memory with the importer’s anchor rules and were not saved. An exact source image means a drawing whose anchor starts on that model row in the photo column (`linked_high`). A drawing that only spans the row, or that starts in another column, is not treated as that product’s photo.

## Scope

| Measure | Count |
| --- | ---: |
| Published products reviewed | 639 |
| Catalog image rows | 542 |
| Products with at least one image | 515 |
| Products with no image | 124 |
| Of those, exact photo-column drawing exists | 40 |
| Of those, only a spanning or off-column drawing | 74 |
| Of those, no drawing on the source row | 10 |
| Products whose stored file is a subset of the row | 39 |
| Stored files whose checksum is not on that row | 0 |
| Checksums shared by more than one product | 84 groups |
| Stored files under 4,000 bytes | 27 |
| Public images with status `high` / `confirmed` | 540 / 2 |
| Products whose only images are hidden from the public site | 0 |

`needs_review` and `rejected` images are not in the catalog. The public site shows `high` and `confirmed` only.

## What was opened

Files were opened and looked at. Byte size was not used as a quality judgment.

Opened from the workbooks: the photo-column drawings for products 3, 5, 8, 13, 25, 37, 110, 184, 200, 289 (three files), 383, 458, 462, 478, 481, 489 (a junction box, CAT6 FTP connector jars, and a power supply from the 21-file set), 522, 524, 525, 548, 554 (both drawings), and 556. Also the extra drawings that are not the repeated ColorVu logo: the plain `NEW` badge, the watermarked `NEW` badge’s sibling already known from Phase 1, a `4G` badge, ColorVu Lite, AcuSense, PanoVu, a near-black square, EZVIZ proximity cards, a crimping tool, and several camera drawings named in the incomplete-set section.

Opened from the catalog: product 56’s only image, the stored BNC photo on product 521, and the small stored files for products 43, 77, 98, 511, 515, 516, 519 (both files), 528, and 549. The public pages for products 56, 521, and 522 were opened in the browser.

The other files under 4,000 bytes were measured (pixel size) and were not opened. They are not called blurry.

## Preserved decisions

These stay as Phase 1 left them.

| Product | Decision | What this pass saw |
| --- | --- | --- |
| 18 `DS-10HKVS-VX1 1TB` | Unverified. Do not attach the shared drawing. | HDD row 17. The drawing `daa444bf…` is a Toshiba label marked 1TB. It is the same file on HDD rows 7–11 and 17. |
| 25 `IPC-B429H (С)` | Do not attach. | Hilook row 9. `26b0863c…` is the ColorVu wordmark, 293×68. |
| 289 `DS-KIS611-S` | Do not attach the set. | Домофоны row 10. Three different drawings. One opened file is an indoor monitor showing 14:02 and Hikvision, with no `DS-KIS611-S`. |
| 489 `DS-1280ZJ-XS` | Do not attach the 21-file set. | `другие устройства` row 36. Opened samples are a junction box, jars labeled CAT6 FTP connector, and a power supply. None is labeled `DS-1280ZJ-XS`. |
| 13, 15, 16, 17 Seagate | Leave without the shared drawing. Product 14 keeps it. | `5c230e2a…` is a Seagate desktop label marked 1000GB, model `ST1000DM003`. It is one file for HDD rows 12 and 14–16 as well as product 14. |
| ColorVu logo and `NEW` badges | Do not add them to galleries. | Confirmed below, including the one badge that is already public. |

## 1. Published products with no image

### Exact photo-column drawing exists (40)

These 40 have a `linked_high` drawing and no catalog image. The public page uses the placeholder. None of these drawings is a safe attach in this pass: each opened file is shared across capacities or models, is a logo, or does not print the model it would be attached to.

| Products | Sheet and rows | File | Opened picture | Action |
| --- | --- | --- | --- | --- |
| 3 `WD30PURX-78`, 4 `WD40PURX-78` | HDD 2–3 | `56ef1361…` | Purple Hikvision/WD label marked 6TB | Keep missing. The label capacity is not 3TB or 4TB. |
| 5 `WD60PURX-78`, 6 `WD80PURX-78`, 7 `WD102PURX-78` | HDD 4–6 | `75b64d44…` | Same kind of purple label, also marked 6TB | Keep missing. One 6TB label cannot stand for 8TB and 10TB. |
| 8 `DS-20HKVS-VXI`, 9 `DS-40HKVS-VXI`, 10 `DS-60HKVS-VXI`, 11 `DS80HKVS‐VX1`, 12 `DS120HKAI-VX1`, 18 `DS-10HKVS-VX1 1TB` | HDD 7–11, 17 | `daa444bf…` | Toshiba 1TB label | Keep missing. |
| 13 `Seagate 500GB`, 15 `Seagate 2TB`, 16 `Seagate 4TB`, 17 `Seagate 6TB` | HDD 12, 14–16 | `5c230e2a…` | Seagate 1000GB label | Keep missing. Approved Seagate decision. |
| 25 `IPC-B429H (С)` | Hilook 9 | `26b0863c…` | ColorVu logo | Keep missing. |
| 37 `IPC-B160HA-LUF/SL` | Hilook 22 | `fa83f324…` | Same drawing also sits on a neighboring model row | Keep missing. |
| 110 `DS-KIS202T`, 111 `VDP-K203` | Hilook 121–122 | `7ca0d559…` | One drawing for two models | Keep missing. |
| 184 `DS-2CD2T83G2-4LI2U 4MM Black` | IP камеры 63 | `d07ed6cc…` | Shared with the neighboring model row | Keep missing. |
| 200 `DS-2CD2687G3-LIZS2UY/SL` | IP камеры 79 | `32a855e5…` | Shared with the neighboring model row | Keep missing. |
| 289 `DS-KIS611-S` | Домофоны 10 | `86ba81c9…`, `ad2f19c9…`, `e00e9228…` | Indoor monitor, plus two other intercom pictures. No model number. | Keep missing. |
| 383 `IDS-TCM403-B` | Проектное оборудование 15 | `22d751c6…` | Shared with the neighboring row | Keep missing. |
| 458 `Andel Q788`, 459 `Cougar Q799` | другие устройства 5–6 | `386a0f08…` | Lock body branded Cougar. It does not print `Q788` or `Q799`. | Keep missing. |
| 462 `Замок 180кг`, 463 `Замок 280кг`, 464 `Замок 350кг` | другие устройства 9–11 | `aa2a77f6…` | One magnetic lock. No force rating. | Keep missing. |
| 478 `Кронштейн 30SMX60SM M-901`, 480 `Кронштейн 60SMX120SM M-901` | другие устройства 25, 27 | `4273e7c0…` | One pedestal for two lengths | Keep missing. |
| 481 `M002` | другие устройства 28 | `87fe713c…` | Two junction-box bases. The sticker is not readable as `M002`. | Keep missing. |
| 489 `DS-1280ZJ-XS` | другие устройства 36 | 21 files | Mixed accessories, including connector jars and a power supply | Keep missing. |
| 522 `BNC` | другие устройства 69 | `d82a029a…` | Short cable tails with gold ends. The picture does not say BNC. | Keep missing. Product 521 is a different BNC row and already has a connector photo. |
| 524 `RG-45 connector CAT6` | другие устройства 71 | `5f332885…` | Jars whose labels read UTP CAT6. The picture is small. | Keep missing until a separate quality decision. The label is readable; the file is still a low-resolution jar photo. |
| 525 `RG-45 CAT6 connector Metall` | другие устройства 72 | `4b2a6509…` | Jars of plugs. The label is not readable as CAT6 or as metal. | Keep missing. |
| 548 `4G R611C` | другие устройства 95 | `ca3966ed…` | MeFi 5G/4G CPE router with a watermark. It does not say `R611C`. | Keep missing. |
| 554 `SMART-16-POE`, 555 `SMART-16-POE Gigabit` | другие устройства 101–102 | `e1bb7d45…` | Generic 16-port PoE switch. No SMART model text. | Keep missing. |
| 554 also | row 101 | `fe3146fb…` | An 8-port switch on a box that says Smart POE Switch. It is also anchored on the 4-port and 8-port rows. | Keep missing. Do not put the 8-port photo on the 16-port row. |
| 556 `SMART-24-POE`, 557 `SMART-24-POE Gigabit` | другие устройства 103–104 | `900cd35f…` | A 24-port switch front. No model text. One file for the standard and Gigabit rows. | Keep missing. |

Confidence for this table is high where the file was opened. The neighboring-row camera files for 37, 184, 200, and 383 were extracted; the association rule, not a second visual claim, is why they stay off. Phase 1 already opened those and found they also sit on a neighboring model.

### No drawing on the source row (10)

There is no source image to add. The placeholder is the correct public state.

| Product | Sheet, row |
| --- | --- |
| 86 `THC-T150-P` | Hilook 84 |
| 296 `DS-KV6124-WBE1` | Домофоны 17 |
| 421 `DS-K1T805MX` | СКУД 20 |
| 527 `RG-45 CAT6 connector` | другие устройства 74 |
| 537 `12V 10A OUTDOOR` | другие устройства 84 |
| 538 `12V 20A OUTDOOR` | другие устройства 85 |
| 539 `12V 30A OUTDOOR` | другие устройства 86 |
| 601 `CS-H90 Dual (4MP+4MP)` | Ezviz 46 |
| 627 `CS-DL06 (WBCP)` | Ezviz 72 |
| 637 `CS-T31-16E-EU Умная розетка` | Ezviz 82 |

### Spanning or off-column drawings only (74)

These products have no photo-column image. The workbook still has 90 `shared_candidate` links and 18 `linked_review` links among them. A shared candidate is a merged photo range that covers extra rows. A linked-review anchor does not start in the photo column. Neither is an exact product photo. They were not attached, and they should not be attached from this inventory.

## 2. Small files and the BNC example

Twenty-seven stored files are under 4,000 bytes. Width and height were empty in the database. Pixel size was read from the files. The previously cited examples were opened:

| Product | File | Pixels | What it shows | Action |
| --- | --- | --- | --- | --- |
| 43 `IPC-B140HA` | `ec964c60…`, 2,139 bytes | 133×59 | HiLook bullet camera | Keep. Small, and the camera is recognizable. Not a blur defect. |
| 56 `IPC-D160HA-LU` | `9029cc55…`, 3,057 bytes | 63×38 | A red `NEW` badge. This is the product’s only image. | Replace the public presentation. See the verified issue below. |
| 77 `THC-B129-LPS` | `5adb6b2a…`, 2,001 bytes | 122×57 | HiLook bullet camera | Keep. Recognizable. |
| 98 `DVR-104U-M1 (S) AcuSense` | `a2e4ced6…`, 2,235 bytes | 141×94 | A small recorder box | Keep. Recognizable. |
| 515 `Панель-заглушка` | `7186753c…`, 1,938 bytes | 162×57 | A blank 1U rack panel | Keep. It matches a blank panel. |
| 521 `BNC` | `c21c1c7a…`, 1,869 bytes | 105×60 | A metal BNC plug | Keep. The public page shows this plug, letterboxed, not cropped. It is soft because the gallery enlarges a 105×60 bitmap to about 542×310. The subject is still a BNC connector. |
| 522 `BNC` | no catalog image; workbook `d82a029a…` | — | Cable tails, not a BNC plug | Do not use that workbook drawing as a sharper replacement for product 521, and do not attach it to 522. |
| 528 `гибкий переход` | `8b7cb283…`, 1,753 bytes | 121×69 | A flexible metal conduit | Keep. Approved image. |
| 549 `SWITTEX 1,8m` | `00f0d668…`, 3,753 bytes | 122×119 | A retail power-strip package | Keep. The object matches a power strip. The package text was not clear enough to call it SWITTEX or LOGA. |

Other opened small catalog files that match their titles and should stay: 511 `Блок розеток` (a rack socket block, 250×84) and 516 `FTP HIGHWAY CAT6` (a box marked HIGHWAY and CAT6, 71×65). Product 519 `FTTH SM2` has two small files: a fiber cross-section (40×68) and a spool marked VIVANCO (64×64). The spool brand is not `FTTH SM2`. That is unresolved, not a confirmed mismatch.

The remaining sub-4,000-byte files were not opened: products 117, 121, 122, 490, 512, 513, 514, 517, 518, 520, 523, 526, 530, 540, and 547. Their pixel sizes are in the same small range. They are not judged blurry.

## 3. Images that may show the wrong subject

Checksum comparison found no stored image that is absent from that product’s own row. A wrong picture, where one exists, is a picture that was on the row and is still the wrong kind of picture.

### Verified

**Product 56 `IPC-D160HA-LU`.** Hilook row. Public URL `hilook-ipc-d160ha-lu`. The only catalog image is `9029cc55adf3…`, object `objects/90/9029cc55adf3a6e7231f626bdaa9cb829d303e5119829bf2e18869507d12c95b.png`, primary, and public. It is a red `NEW` badge, 63×38. The live page renders it at about 542×327 with `object-fit: contain` and no CSS filter. The page heading and description are the 6 MP dome camera. The badge does not depict that camera. The row has no second drawing to put in its place. Confidence: high.

The same badge is an extra drawing on products 33, 41, 54, 55, 57, and 60. Those products already have a product photo. Do not add the badge to them.

### Not verified as wrong

Shared drive labels, the ColorVu logo, the Cougar lock, the magnetic lock, the switches, the MeFi router, and the cable tails are wrong or incomplete associations only if they were attached. They are not attached, except the Seagate 1000GB label, which stays on product 14 by the approved decision.

Product 519’s VIVANCO spool is the only stored file in this pass whose visible brand does not match the model name. It was not reclassified, because a fiber spool can still be the product and the model text is not printed on the photo.

## 4. Extra workbook drawings on products that already have a photo

Thirty-nine products store one photo-column drawing and lack at least one other. The stored checksum is one of the row’s drawings. The missing files were grouped and opened. They are not a second confirmed product photo.

| Missing file | Where it is the extra | What it shows | Action |
| --- | --- | --- | --- |
| `26b0863c…` | 52 products, including most of the 39 | ColorVu logo | Do not add. |
| `04f0dea1…` | 563, 567, 568, 583, 595, 616 | `NEW` badge with a stock-site watermark | Do not add. |
| `9029cc55…` | 33, 41, 54, 55, 57, 60, and it is already the only image on 56 | Plain `NEW` badge | Do not add. Remove it from 56. |
| `98a072be…` | 592, 595, 604, 605, 607, 611 | A `4G` badge | Do not add. |
| `b1753782…` | 238, 277, 345, 490, 516 | ColorVu Lite logo | Do not add. |
| `89f7eeb1…` | 69 `IPC-C341 G2`, 70 `IPC-C361 G2` | AcuSense wordmark | Do not add. |
| `6644558d…` | 106 | PanoVu wordmark | Do not add. |
| `fc2523fc…` | 607, 610 | A near-black square | Do not add. |
| `5e832a5f…` | 511 `Блок розеток` | A crimping tool. The stored image is already the socket block. | Do not add. |
| `0866e02b…` | 634 `CS-DL-IC-CPU-R200` | EZVIZ proximity cards, a pack of 4 | Needs verification. The cards do not print that model. |
| `fe3146fb…` | 552 `SMART-04-POE`, 553 `SMART-08-POE`, and also on 554 | 8-port switch | Do not add to the 4-port or 16-port rows. Not confirmed for the 8-port row either. |
| `5200e726…` | 71 `IKS-2044BTH-PH/W`, 72 `IKS-2044BPH-PH/W` | A HiLook cube camera. The same file is already stored on 67 `IPC-C320` and 68 `IPC-C340`. | Do not add it to the intercom rows. |
| `7a7c9743…` | 172 `DS-2CD2347G2-LU` | A black camera branded HiLook | Do not add to this Hikvision model. |
| `9b630cf6…` | 239 and 240, both `DS-2CD1F47…` | A white HiLook bullet | Do not add. |
| `be93393d…` | 237 `DS-2CFSP4/4G` | A HiLook turret | Do not add. |
| `f092786c…` | 24 `IPC-B129HA-LU` | A HiLook bullet without the light bar. Product 24 already stores a HiLook bullet with a light bar (`610bed62…`). | Do not add. It is a different view or a different variant, and the model is not printed. |
| `d8092e63…` | 63 `IPC-B640HA-LZU/SL` | A HiLook dome | Needs verification. The form does not by itself prove this zoom model. |
| `db38bc0a…` | 591 `CS-H8C (4MP)` | An EZVIZ turret. The same file is already public on 592–596, which are other H8c models. | Do not add. One turret is already standing for five models. |
| `d87e51bc…` | 606 `CS-EB8 Pro Ranger (8MP)` | An EZVIZ camera with a solar panel | Needs verification. It matches the product class and does not print the model. |
| `a4d39c8e…` | 288 `DS-KIS610-P` | A Hikvision door station. No kit model is printed. | Needs verification. Same caution as product 289. |
| `86ba81c9…` | 288 and 290 | The indoor monitor also anchored on product 289 | Do not add. |

No incomplete row is missing a second photo that both shows the same object and prints that model.

## 5. Duplicated files

Eighty-four checksums are already stored on more than one product. A shared file is not an error. The largest stored groups are channel or lens variants of one family, for example six NVR models from `DS-7604NXI-K1/VPro` through `DS-7632NXI-K2` on `e5cd894d…`, and five `DS-7604NI-Q1` / `DS-7608NXI-K1` recorders on `4ea813dc…`. Products 267 and 268 remain the approved shared PTZ pair. These groups were not split and were not called wrong.

The suspicious duplicates are the ones that are not stored on the mismatched products: one 6TB label across 3TB–10TB rows, one Toshiba 1TB label across six Hikvision capacities, and one Seagate 1000GB label across 500GB–6TB. Those stay unattached except product 14.

`db38bc0a…`, the EZVIZ turret, is stored on five H8c models (592–596). That is legitimate only as a shared body photo. It should not be spread to a sixth model from this audit.

## 6. Public presentation

Product cards, the homepage cards, and the product gallery use `object-contain`. There is no `object-cover`, no blur filter, and no rule that stretches a bitmap to a different aspect. A browser check confirmed `object-fit: contain` and `filter: none` on products 56 and 521. The rendered box kept the file’s own aspect ratio.

The gallery and the cards do enlarge a small bitmap until it meets the column width. Product 56’s 63×38 badge is drawn at about 542×327. Product 521’s 105×60 connector is drawn at about 542×310. That enlargement is why a sharp-enough small photo looks soft. It is not cropping.

Products with no public image use a light panel. On product 522 the panel reads `Нет изображения`. The same component uses `Rasm yo'q` and `No image` in the other locales, with a camera glyph in the markup. Catalog cards use the same empty state at a fixed height (`h-52` on catalog cards, `h-40` on homepage cards). The homepage hero and featured picks skip products that have no image, so the homepage does not show an empty frame for them.

Stored width and height are null on the small files. The page supplies 960×720 when those values are missing. On the two pages that were measured, the displayed box still followed the file’s real aspect, so the fallback attributes did not stretch those two images.

## 7. Placeholders

The placeholder is appropriate for the 10 products with no source drawing, the 74 products with only a spanning or off-column drawing, and the 40 products whose exact drawing was inspected and rejected. It is also the right replacement for product 56 until a real camera photo exists.

## Prioritized corrections that are safe

1. **Product 56 `IPC-D160HA-LU`.** Stop publishing `9029cc55…` as the product photo. The row has no other drawing. The honest result is the existing placeholder. Do not invent a camera image, and do not attach the badge to products 33, 41, 54, 55, 57, or 60.
2. **Presentation, without changing files.** Keep `object-contain`. Avoid enlarging a bitmap far past its pixel size in the gallery and on cards, so a 105×60 connector and the other small-but-correct photos are not blown up to the full column. This is a display change, not an image replacement.

No other catalog image should be attached, removed, or reassigned from this audit.

## Needs more evidence

- Product 18, including any photo. The Toshiba label stays off.
- Products 25, 289, and 489, and every shared drawing in the 40-row table.
- The approved Seagate choice: product 14 keeps `5c230e2a…`; 13, 15, 16, and 17 stay without it.
- Product 524’s CAT6 jar, if someone later accepts a small but readable photo.
- Product 519’s VIVANCO spool against the model `FTTH SM2`.
- Extra camera-like files that do not print the model: the dome on 63, the solar camera on 606, the door station on 288, and the proximity cards on 634.
- The 15 sub-4,000-byte files that were measured and not opened. They are not a blur finding.
- The 74 spanning and off-column links. They are not exact photos.

## What this audit did not do

No image was uploaded, deleted, or reassigned while the inventory was written. No product, price, description, category, or publication flag was edited. The workbooks were not saved. No import was applied. No migration ran. No service was restarted. Nothing was committed, pushed, or deployed.

## First approved batch — completed

18 October 2026. Only the two corrections listed under “Prioritized corrections that are safe” were applied. No other finding in this audit was treated as fixed.

### Product 56, IPC-D160HA-LU

The public association with the red `NEW` badge was removed through the existing admin route `DELETE /api/admin/products/{id}/images/{image_id}`. That route deletes the `product_images` row and writes `admin_audit_log.action = image_removed`. It does not unlink the media file.

- The file remains at `objects/90/9029cc55adf3a6e7231f626bdaa9cb829d303e5119829bf2e18869507d12c95b.png` (3,057 bytes).
- No `product_images` row still uses that checksum. Eighty-four `import_assets` rows still point at the same object key, and none of them proposes a product, so the file was not deleted.
- Product 56 is unchanged apart from that association: model `IPC-D160HA-LU`, slug `hilook-ipc-d160ha-lu`, price 53.00 USD, brand 4, category 5, empty option, status `published`. Source record: `Hikvision pr.xlsx`, worksheet `Hilook`, row 44. English and Uzbek descriptions stay locked with origin `manual`; the Russian description stays unlocked with origin `source`.
- Catalog image rows went from 542 to 541. Published products remain 639. Spot-checked associations that were not touched: product 14 image 12 (`5c230e2a…`), product 43 image 39 (`ec964c60…`), product 77 image 75 (`5adb6b2a…`), product 521 image 543 (`c21c1c7a…`).
- With no public image, the existing gallery placeholder is shown. Checked on the dev server for this source tree: Russian `Нет изображения`, Uzbek `Rasm yo'q`, English `No image`. Each page has zero product images. The same Russian, Uzbek, and English placeholders were also present on the live site.

No replacement drawing was attached.

### Small rasters are not enlarged

`ProductPhoto` is the shared public image. It keeps `object-contain`, uses `h-auto w-auto`, and caps the box with `max-h-full max-w-full` in cards and thumbnails or `max-h-[32rem] max-w-full` in the gallery. Width and height attributes are passed through only when both stored values are positive numbers. Otherwise they are omitted, so a missing database size does not invent a 640×480 or 960×720 stand-in. Card, hero, search, and thumbnail frames keep their existing heights, and the photo is centered inside them.

Checked in the browser against this source tree, at a 1920px desktop width and a 390px phone width:

| Surface | File pixels | Displayed | Result |
| --- | ---: | ---: | --- |
| Product 521 gallery, desktop and phone | 105×60 | 105×60 | Not enlarged. `object-fit: contain`. |
| CS-H1C gallery, desktop | 3508×2480 | 592×419 | Downscaled to the column. Aspect kept. |
| CS-H1C gallery, phone | 3508×2480 | 325×230 | Downscaled. Fills most of the 390px width. |
| IPC-B469HAD-LUF/SL gallery, desktop | 335×142 | 335×142 | Intrinsic size. Second photo, 493×222, switches in from the thumbnail. |
| IPC-B469HAD-LUF/SL gallery, phone | 335×142 | 325×138 | Slightly downscaled to the column, not enlarged. Thumbnails stay inside the `h-20` buttons. |
| Cable category cards | 105×60 and other small files | intrinsic pixels | Centered in the existing `h-52` frame. |
| Homepage NVR card | 620×405 | 244×159 | Fills the card height and is downscaled. |
| Homepage PoE card | 504×222 | 361×159 | Fills the card and is downscaled. |
| Homepage small camera cards | 135×86 and 99×67 | intrinsic pixels | Not enlarged inside the existing card frame. |

### Validation

- `npm run typecheck` (`tsc --noEmit`) passed.
- `node --experimental-strip-types --test` on `product-photo.test.mts`, `home-featured.test.mts`, and `home-search.test.mts`: 14 passed.

### Still limited

- The site on port 8080 and the preview on port 3010 still serve the previous frontend build. The sizing change is in source and was measured on a dev server at port 3012. Compose services were not rebuilt or restarted.
- Product 56 has no genuine camera photo. The placeholder is the intended result. English and Uzbek titles still fall back to the Russian name because `localized_name` is empty. That text was not changed.
- A tiny photo sits inside the gallery’s `min-h-80` frame and the cards’ fixed heights, so those slots keep some empty space around a small file. Large photos still fill the slot and are only scaled down.
- Stored width and height are often null. The component then uses the file’s intrinsic pixels plus the max constraints.
- No other image in this audit was attached, removed, or reassigned. The workbooks were not saved. No import or migration ran. Nothing was committed, pushed, or deployed.
