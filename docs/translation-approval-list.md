# Translation approval list — 24 Cyrillic UZ/EN product titles

**Date:** 19 October 2026
**Source finding:** `docs/multilingual-catalog-audit.md` section B1
**Checkpoint context:** live local catalog (read-only). No database rows, code, workbooks, imports, commits, pushes, or deploys were changed while preparing this list.

**Purpose:** Propose concise Uzbek and English `localized_name` values for human approval before any catalog edit.

**Rules used:**
- Prefer wording already present in the product’s approved UZ/EN **description**.
- Keep model codes and size tokens (`T311`, `EM-Marine`, `CS-SD7`, `20SM`, `M-611`, etc.).
- For service rows 638–641, keep one shared title per retention period; billing stays on `option_label` (monthly vs yearly).
- Mark **human review** where the short title is not spelled out in the description, or UZ terminology is ambiguous.
- Do not invent technical specifications.

**Confidence scale:**
- **high** — short name is a direct trim of the locale description (or Latin-only model normalization).
- **medium** — supported by description + Russian title sense, but short form needs a preference choice.
- **low / deferred** — not enough reliable wording for a short title without guessing.

---

## Summary

| Bucket | Count | IDs |
|--------|------:|-----|
| Approved in migration `approved_uz_en_product_names` | **17** products (**34** UZ/EN names) | 444, 445, 462, 463, 464, 468, 477, 478, 479, 480, 511, 513, 514, 638, 639, 640, 641 |
| Deferred for human review (not in the migration) | **7** | **25, 469, 512, 515, 621, 636, 637** |
| No reliable short title without guessing | 0 | — |

All 24 rows below still have non-blank UZ and EN descriptions and keep their evidence and proposed wording for review. The Alembic data migration applies **only** the 17 high-confidence products above (both `uz` and `en` for each). Product **515** is **not** included—neither its English nor its Uzbek proposed name ships in that migration. The seven deferred IDs stay blank in the catalog until a later human decision.

---

## Review table

| ID | Slug | Russian name | Proposed Uzbek name | Proposed English name | Supporting evidence | Confidence |
|---:|------|--------------|---------------------|-----------------------|---------------------|------------|
| 25 | `hilook-ipc-b429h-s` | `IPC-B429H (С)` | `IPC-B429H (C)` | `IPC-B429H (C)` | Hilook / 9. Model is Latin except Cyrillic `С` in parentheses. Descriptions do not redefine the model string. Audit B1 note: likely Latin `C`. **Confirm character normalization only. Deferred — not in the approved migration.** | deferred (human review) |
| 444 | `product-turniket-t311` | `Турникет T311` | `T311 tripod turniket` | `T311 tripod turnstile` | СКУД / 43. EN desc: `T311 tripod turnstile.` UZ desc: `T311 tripod turniket.` RU desc: `Турникет-трипод T311`. | high (in migration) |
| 445 | `product-turniket-t315` | `Турникет T315` | `T315 portal turniket` | `T315 portal turnstile` | СКУД / 44. EN desc: `T315 portal turnstile.` UZ desc: `T315 portal turniket.` RU desc: `Турникет-портал T315`. | high |
| 462 | `product-zamok-180kg` | `Замок 180кг` | `180 kg elektromagnit qulf` | `180 kg electromagnetic lock` | другие устройства / 9. EN desc: `180 kg electromagnetic lock.` UZ desc: `180 kg elektromagnit qulf.` | high |
| 463 | `product-zamok-280kg` | `Замок 280кг` | `280 kg elektromagnit qulf` | `280 kg electromagnetic lock` | другие устройства / 10. Same pattern as 462 in EN/UZ descriptions. | high |
| 464 | `product-zamok-350kg` | `Замок 350кг` | `350 kg elektromagnit qulf` | `350 kg electromagnetic lock` | другие устройства / 11. Same pattern as 462 in EN/UZ descriptions. | high |
| 468 | `product-karta-em-marine` | `карта EM-Marine` | `Kontaktsiz EM-Marine karta` | `Contactless EM-Marine card` | другие устройства / 15. EN desc: `Contactless EM-Marine card.` UZ desc: `Kontaktsiz EM-Marine karta.` Keep `EM-Marine`. | high |
| 469 | `product-brelok` | `Брелок` | `Magnit brelok` | `Magnetic key fob` | другие устройства / 16. EN desc: `Emarine and Mifare magnetic key fob.` UZ desc: `Emarine va Mifare magnit brelok.` Short title omits protocol brands (remain in description). **Confirm** whether to include `Emarine / Mifare` in the name. **Deferred — not in the approved migration.** | deferred (human review) |
| 477 | `product-kronshteyn-20sm-m-611` | `Кронштейн 20SM M-611` | `Kronshteyn 20SM M-611` | `Bracket 20SM M-611` | другие устройства / 24. EN/UZ/RU descriptions already use this exact short form (`Bracket` / `Kronshteyn` + tokens). | high |
| 478 | `product-kronshteyn-30smx60sm-m-901` | `Кронштейн 30SMX60SM M-901` | `Kronshteyn 30SMX60SM M-901` | `Bracket 30SMX60SM M-901` | другие устройства / 25. Descriptions match; keep `30SMX60SM` and `M-901` as stored. | high |
| 479 | `product-kronshteyn-30sm-m-612` | `Кронштейн 30SM M-612` | `Kronshteyn 30SM M-612` | `Bracket 30SM M-612` | другие устройства / 26. Descriptions match. | high |
| 480 | `product-kronshteyn-60smx120sm-m-901` | `Кронштейн 60SMX120SM M-901` | `Kronshteyn 60SMX120SM M-901` | `Bracket 60SMX120SM M-901` | другие устройства / 27. Descriptions match; keep `60SMX120SM`. | high |
| 511 | `product-blok-rozetok` | `Блок розеток` | `Rozetkalar bloki` | `Socket block` | другие устройства / 58. UZ desc opens `Rozetkalar bloki…`. EN desc opens `Socket block 19"…`. Phase-2 image audit: rack socket block. Specs stay in description. | high |
| 512 | `product-falshpanel` | `фальшпанель` | `Cho'tkali soxta panel` *(or prefer another UZ term)* | `Blank panel` | другие устройства / 59. EN desc: `Blank panel with a brush entry for a 19" cabinet, 1U.` UZ desc: `19" shkafga cho'tkali kiritishli soxta panel, 1U.` Short EN from leading noun phrase. **UZ:** confirm `soxta panel` vs catalog synonym; brush entry can stay in description. **Deferred — not in the approved migration.** | deferred (human review) |
| 513 | `product-patch-panel` | `Патч-панель` | `Patch panel` | `Patch panel` | другие устройства / 60. EN and UZ descriptions both start with `Patch panel`. | high |
| 514 | `product-organayzer` | `органайзер` | `Kabel organayzeri` | `Cable organizer` | другие устройства / 61. EN desc: `Cable organizer with metal rings…`. UZ desc: `Metall halqalar va qopqoqli kabel organayzeri…`. | high |
| 515 | `product-panel-zaglushka` | `Панель-заглушка` | `Panel-tiqin` *(confirm)* | `Blanking panel` | другие устройства / 62. EN desc: `Blanking panel, 1U, black.` UZ desc: `1U qora panel-tiqin.` Distinguish from 512 (brush blank panel). **Deferred:** UZ short form needs preference; EN was previously listed as high-confidence but is **not** in the approved migration until both locales are decided together. | deferred (human review) |
| 621 | `ezviz-cs-sd7-umnyy-ekran` | `CS-SD7 Умный экран` | `CS-SD7 aqlli ekran` | `CS-SD7 Smart screen` | Ezviz / 66. Keep `CS-SD7`. EN/UZ descriptions describe a touch / smart display but do not spell the retail short title; wording follows RU «Умный экран» + existing description sense. **Confirm marketing label. Deferred — not in the approved migration.** | deferred (human review) |
| 636 | `ezviz-cs-t30-10b-eu-umnaya-rozetka` | `CS-T30-10B-EU Умная розетка` | `CS-T30-10B-EU aqlli rozetka` | `CS-T30-10B-EU Smart plug` | Ezviz / 81. Keep full model `CS-T30-10B-EU`. Descriptions cover app / Wi‑Fi control; short “smart plug/rozetka” mirrors RU title, not a literal EN desc headline. **Confirm “plug” vs “socket”. Deferred — not in the approved migration.** | deferred (human review) |
| 637 | `ezviz-cs-t31-16e-eu-umnaya-rozetka` | `CS-T31-16E-EU Умная розетка` | `CS-T31-16E-EU aqlli rozetka` | `CS-T31-16E-EU Smart plug` | Ezviz / 82. Same pattern as 636; model `CS-T31-16E-EU`. **Deferred — not in the approved migration.** | deferred (human review) |
| 638 | `ezviz-7-dnevnaya-videoistoriya-sobytiy-ezhemesyachno` | `7-дневная видеоистория событий` | `7 kunlik voqealar videotarixi` | `7-day video event history` | Ezviz / 83. `product_kind=service`, `option_label=Ежемесячно:`. EN desc: `Service: 7-day video event history. Billing: monthly.` UZ desc quotes `7 kunlik voqealar videotarixi`. Do **not** merge with 640. | high |
| 639 | `ezviz-30-dnevnaya-videoistoriya-sobytiy-ezhemesyachno` | `30-дневная видеоистория событий` | `30 kunlik voqealar videotarixi` | `30-day video event history` | Ezviz / 84. Monthly service. EN/UZ descriptions use the same service title pattern as 638/641. Do **not** merge with 641. | high |
| 640 | `ezviz-7-dnevnaya-videoistoriya-sobytiy-ezhegodno` | `7-дневная видеоистория событий` | `7 kunlik voqealar videotarixi` | `7-day video event history` | Ezviz / 85. Yearly twin of 638 (`option_label=Ежегодно:`). Same localized name as 638; billing differs only by option. | high |
| 641 | `ezviz-30-dnevnaya-videoistoriya-sobytiy-ezhegodno` | `30-дневная видеоистория событий` | `30 kunlik voqealar videotarixi` | `30-day video event history` | Ezviz / 86. Yearly twin of 639. Same localized name as 639. | high |

---

## Deferred for human review (not in migration `approved_uz_en_product_names`)

These seven IDs still have proposed text and evidence above, but they were **intentionally omitted** from the approved-name migration. An approver should decide before any later apply:

| ID | Decision needed |
|---:|-----------------|
| 25 | Normalize Cyrillic `(С)` → Latin `(C)` in UZ/EN (and optionally RU), or leave model string unchanged. |
| 469 | Short `Magnetic key fob` / `Magnit brelok` vs include `Emarine` / `Mifare` in the title. |
| 512 | Preferred Uzbek noun for blank/false panel (`soxta panel` vs other site terminology). |
| 515 | Preferred Uzbek short form (`Panel-tiqin` vs another blanking-panel term); keep distinct from 512. English `Blanking panel` is also deferred—**not** part of the approved migration. |
| 621 | Confirm `Smart screen` / `aqlli ekran` as the retail short name beside `CS-SD7`. |
| 636, 637 | Confirm English `Smart plug` vs `Smart socket` / `Smart outlet`. |

No product in this set lacks enough description text to support *some* evidence-based short name. None are marked “cannot determine.”

---

## Context preserved from the audits (do not re-apply blindly)

- Categories: `colorvu`, `skud`, `montazhnye-prinadlezhnosti`, `komplektuyushchie-dlya-shkafov`, `ezviz` as listed above.
- Workbooks: Hikvision `Hikvision pr.xlsx` (Hilook / СКУД / другие устройства) and EZVIZ `Ezviz pr.xlsx` (Ezviz sheet).
- Product **528** is **out of scope** here (titles already localized per multilingual audit).
- After approval, apply only via the established admin/data path; do not bulk-edit from this document alone.

---

## Suggested apply checklist

**Already applied (17 products / 34 names):** migration `approved_uz_en_product_names` via `api/app/data/approved_uz_en_product_names.py` (high-confidence IDs in the summary). Descriptions were left unchanged.

**After the seven deferred IDs are approved:**

1. Set `product_translations.localized_name` for `uz` and `en` to the approved strings (leave `description` unchanged unless separately approved)—via a follow-up data migration or the established admin path; do not bulk-edit from this document alone.
2. Optionally normalize ID 25’s model/parenthetical character if that decision is approved.
3. Re-check public API: `translation_fallback` false for UZ/EN; `<title>` and image alts no longer Cyrillic on those locales.
4. Keep 638/640 and 639/641 as separate rows with identical names and distinct `option_label`.

---

*End of translation approval list.*
