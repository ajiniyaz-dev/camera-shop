# Catalog accuracy review

Read-only check on 17 October 2026 of the 13 findings requested from `docs/catalog-accuracy-audit.md`. `data/source/Hikvision pr.xlsx` was opened and not saved. The catalog text was read from the database the public site uses. This review published, edited, imported, migrated, committed, or pushed nothing. The later correction of products 433 and 434 is recorded after the table.

All 13 findings were verified. None is left unverified.

The description column on these sheets is `Характеристика` (column D). Row 1 is the header. Columns A–K were read for every row below. No merged range covers those cells, and none of the cells has a comment. A claim quoted here is absent from the description cell, not inferred from a neighboring row.

Where a source-supported correction is available, it is only the change that makes the catalog match the cell. Keeping a claim the cell does not contain is marked **Needs decision**.

## Review table

| Product | Workbook, sheet, row, cell | Exact source cell | Exact catalog value | Discrepancy | Suggested correction |
| --- | --- | --- | --- | --- | --- |
| 18 `DS-10HKVS-VX1 1TB` | `Hikvision pr.xlsx`, HDD, row 17, `D17` | Empty | ru: `Жесткий диск Hikvision для видеонаблюдения DS-10HKVS-VX1, 1 ТБ.` uz: `Hikvision videokuzatuv qattiq diski DS-10HKVS-VX1, 1 TB.` en: `Hikvision surveillance hard drive DS-10HKVS-VX1, 1 TB.` | The whole sentence is absent from `D17`. `C17` is `DS-10HKVS-VX1     1TB`, so the capacity token is in the model cell. The words for “surveillance hard drive” are not in `C17` or `D17`. | Clear the three descriptions so they match empty `D17`. Keeping the sentence: **Needs decision**. |
| 433 `DS-K6B411TMX-M` | `Hikvision pr.xlsx`, СКУД, row 32, `D32` | Empty | At review, Russian included `около 30–40 чел/мин` and `~0.2–0.5 сек` in the paragraph quoted below. Uzbek and English repeated both. | Absent from `D32`. `C32` is only `DS-K6B411TMX-M`. The Excel cell was not changed. | Corrected 18 October 2026. See the note after this table. The two numerical claims were removed. The rest of the paragraph was kept. |
| 434 `DS-K6B411TMX-R` | `Hikvision pr.xlsx`, СКУД, row 33, `D33` | Empty | At review, the same Russian, Uzbek, and English paragraphs as product 433, including both numerical claims. | Absent from `D33`. `C33` is only `DS-K6B411TMX-R`. The Excel cell was not changed. | Corrected 18 October 2026 with the same removal as product 433. |
| 437 `DS-K3B501SX-M/M` | `Hikvision pr.xlsx`, СКУД, row 36, `D36` | Empty | `Профессиональные качели-барьеры. 12 пар ИК-детекторов: проверка разрешений и защита от несанкционированного прохода. Светодиодный индикатор указывает направление движения. Звуковая и визуальная сигнализация защемления: шлагбаум прекращает работу на определенный период времени при обнаружении препятствия при открытии/закрытии шлагбаума. Самообнаружение, самодиагностика и автоматическая сигнализация. Настройки допустимой продолжительности проезда: система отменит разрешение на проезд, если человек не проедет по полосе в течение допустимой продолжительности проезда. Дверь остается открытой при срабатывании пожарной сигнализации: Барьер откроется автоматически при срабатывании пожарной сигнализации. Барьер находится в свободном состоянии при отключении питания.` | Absent from `D36`. `C36` is only `DS-K3B501SX-M/M`. Unsupported count: `12 пар ИК-детекторов`. Uzbek says `12 juft IQ detektor`. English says `12 pairs of IR detectors`. | Clear the three descriptions so they match empty `D36`. Keeping them: **Needs decision**. |
| 438 `DS-K3B501SX-R/M` | `Hikvision pr.xlsx`, СКУД, row 37, `D37` | Empty | Same Russian, Uzbek, and English text as product 437. | Absent from `D37`. `C37` is only `DS-K3B501SX-R/M`. Same unsupported count: `12 пар ИК-детекторов`. | Clear the three descriptions so they match empty `D37`. Keeping them: **Needs decision**. |
| 441 `DS-K3B211LX-M` | `Hikvision pr.xlsx`, СКУД, row 40, `D40` | Empty | `турникет стеклянный : 4 пары ИК-датчиков света: проверка разрешений и защита от несанкционированного доступа. Светодиодный индикатор указывает направление движения. Настройки допустимой продолжительности проезда: система отменит разрешение на проезд, если человек не проедет по полосе в течение допустимой продолжительности проезда. Дверь остается открытой при срабатывании пожарной сигнализации: дверные створки будут иметь статус свободных.` | Absent from `D40`. `C40` is only `DS-K3B211LX-M`. Unsupported count: `4 пары ИК-датчиков света`. Uzbek says `4 juft IQ yorug'lik datchigi`. English says `4 pairs of IR light sensors`. | Clear the three descriptions so they match empty `D40`. Keeping them: **Needs decision**. |
| 442 `DS-K3B211LX-L` | `Hikvision pr.xlsx`, СКУД, row 41, `D41` | Empty | Same Russian, Uzbek, and English text as product 441. | Absent from `D41`. `C41` is only `DS-K3B211LX-L`. Same unsupported count: `4 пары ИК-датчиков света`. | Clear the three descriptions so they match empty `D41`. Keeping them: **Needs decision**. |
| 447 `DRT-ES3216 Middle` | `Hikvision pr.xlsx`, СКУД, row 46, `D46` | Empty | `Габариты -1400*160*980 мм. скорость движения В часы работы: 50 человек/мин; В обычное время закрытия: 35 человек/мин. Трехцветная RGB-подсветка. Упрощенная плата с бесщеточным двигателем 1V2 + блок управления электроникой + плата с сетевым портом. Рабочая температура -20℃~+70℃. источник питания 24 В 150 Вт.` | Absent from `D46`. `C46` is only `DRT-ES3216 Middle`. Unsupported values: `1400*160*980 мм`, `50 человек/мин`, `35 человек/мин`, `1V2`, `-20℃~+70℃`, `24 В 150 Вт`. Uzbek and English repeat them. | Clear the three descriptions so they match empty `D46`. Keeping them: **Needs decision**. |
| 448 `DRT-ES3216 Right` | `Hikvision pr.xlsx`, СКУД, row 47, `D47` | Empty | Same Russian, Uzbek, and English text as product 447. | Absent from `D47`. `C47` is only `DRT-ES3216 Right`. Same unsupported values as product 447. | Clear the three descriptions so they match empty `D47`. Keeping them: **Needs decision**. |
| 451 `DS-TMG320-LR` | `Hikvision pr.xlsx`, СКУД, row 50, `D50` | Empty | `Шлагбаумы серии 32. Обеспечивает удобную боковую установку благодаря компактной конструкции. Используется маломощный бесщеточный двигатель постоянного тока с низким уровнем шума для увеличения крутящего момента и обеспечения точного интеллектуального управления. Функция задержки закрытия стрелы. Поддерживается задержка от 1 до 600 секунд. Поддерживает Bluetooth-соединение с приложением для смартфона для настройки шлагбаума. Стандартизированный патрон, один патрон подходит для всех типов мачт.` | Absent from `D50`. `C50` is only `DS-TMG320-LR`. Unsupported values: `серии 32` and `от 1 до 600 секунд`. Uzbek and English repeat both. | Clear the three descriptions so they match empty `D50`. Keeping them: **Needs decision**. |
| 453 `DS-TMG320-LR-B` | `Hikvision pr.xlsx`, СКУД, row 52, `D52` | Empty | The product 451 paragraph, plus `Корпус шлагбаума оснащен изящными индикаторными лампочками, позволяющими с первого взгляда оценить состояние шлагбаума.` | Absent from `D52`. `C52` is only `DS-TMG320-LR-B`. Same unsupported `серии 32` and `от 1 до 600 секунд`, plus the indicator-lamp sentence, which is also absent. Uzbek and English include that extra sentence. | Clear the three descriptions so they match empty `D52`. Keeping them: **Needs decision**. |
| 549 `LOGA 5/1,8м` | `Hikvision pr.xlsx`, другие устройства, row 96, `C96` | `SWITTEX 1,8m` | Model and Russian title: `LOGA 5/1,8м`. Russian description matches `D96` exactly: `Сетевой фильтр LOGA 5/1,8м с з/к с выключателем Цвет: Белый Производитель: LOGA Допустимый ток: 10 А Количество гнёзд: 5 Заземление: Да Наличие кнопки: Да Длина провода: 1,8м` | `C96` and `D96` disagree. The model cell says `SWITTEX 1,8m`. The description cell names `LOGA 5/1,8м`. The catalog model follows the description cell. The stored source model is still `SWITTEX 1,8m`, and the public slug is `product-swittex-1-8m`. | **Needs decision**. The workbook does not establish one model. |
| 449 `DRT-Z-310` | `Hikvision pr.xlsx`, СКУД, row 48, `D48` | `Процент сдачи экзамена: 35 пенсов в месяц` | Russian: `Пропускная способность: 35 человек в минуту`. Uzbek: `O'tkazish qobiliyati: daqiqasiga 35 kishi.` English: `Pass rate: 35 persons per minute.` | One sentence was replaced. The number 35 remains. The claim changed from `пенсов в месяц` to people per minute. The rest of the Russian description matches `D48`. | Restore the Russian sentence from `D48`. What Uzbek and English should say for that sentence: **Needs decision**. |

## Products 433 and 434 after the review

The catalog values in the table are the 17 October text. The original Russian paragraph on both products was:

`Стеклянный турникет (swing-барьер) премиум-класса. Корпус из нержавеющей стали, прозрачные створки. Высокая пропускная способность — около 30–40 чел/мин. Быстрое открытие створок — ~0.2–0.5 сек. Бесщеточный мотор, плавное и тихое движение. Поддержка карт и распознавания лиц. Встроенные датчики безопасности и анти-tailgating. Аварийное автоматическое открытие при пожаре.`

On 18 October 2026 those two numerical sentences were removed from Russian, Uzbek, and English. Audit entry 1635 records the update for product 433, and audit entry 1636 records it for product 434. The 5–60 second door-open duration was not added. `D32` and `D33` are still empty, and `source_description_raw` still contains the paragraph above, including the two claims. It was not rewritten to match the published text.

The current Russian description on both products is: `Стеклянный турникет (swing-барьер) премиум-класса. Корпус из нержавеющей стали, прозрачные створки. Бесщеточный мотор, плавное и тихое движение. Поддержка карт и распознавания лиц. Встроенные датчики безопасности и анти-tailgating. Аварийное автоматическое открытие при пожаре.` Uzbek: `Premium-klass shisha turniket (swing-to'siq). Zanglamaydigan po'lat korpus, shaffof qanotlar. Cho'tkasiz motor, ravon va tinch harakat. Kartalar va yuzni tanish qo'llab-quvvatlanadi. O'rnatilgan xavfsizlik datchiklari va anti-tailgating. Yong'inda avariya holatida avtomatik ochilish.` English: `Premium glass turnstile (swing barrier). Stainless-steel housing, transparent leaves. Brushless motor, smooth and quiet movement. Cards and face recognition are supported. Built-in safety sensors and anti-tailgating. Automatic emergency opening in a fire.` The public pages were checked in all three languages.

## Exact `D48` text

The cell, including its line breaks, is:

```
Материал: нержавеющая сталь SUS304 толщиной 1,2/1,0 мм. Размер: 200*200*980 мм. Количество пар датчиков: 5 пар. Процент сдачи экзамена: 35 пенсов в месяц
Ширина прохода: 600-900 мм
Входное напряжение: 100–240 В
Тип двигателя: щеточный двигатель постоянного тока
Условия окружающей среды: -20~+70
Источник питания: 24 В 150 Вт
Вес нетто: 30 кг
```

`C48` is `DRT-Z-310 ` with a trailing space. The catalog model is `DRT-Z-310`. That spacing difference is the importer’s normal collapse and is not a separate finding. The stored source description still has the `пенсов` sentence. The published Russian description does not.

## Stored source copy

For products 437, 438, 441, 442, 447, 448, 451, and 453, the database field `source_description_raw` contains the catalog paragraph. The Excel cells listed above are empty. The workbook cell is the source value in this review. The stored field does not reproduce it. For products 433 and 434, `source_description_raw` still contains the pre-correction paragraph quoted above. It matches neither the empty Excel cell nor the description now published.

Product 18’s stored source description is empty, which matches `D17`. Product 449’s stored source description still matches `D48`. Product 549’s stored source model still matches `C96`, and its stored source description still matches `D96`.

## Verified count and open questions

13 findings verified. 0 unverified.

Open questions, with no value chosen:

- For the empty description cells other than products 433 and 434, whether to clear the catalog text or keep claims the workbook does not contain. Products 433 and 434 had only the two numerical claims removed. Their remaining sentences were kept.
- For product 549, whether the sold model is `SWITTEX 1,8m` from `C96` or `LOGA 5/1,8м` from `D96`.
- For product 449, whether to restore `35 пенсов в месяц` or keep `35 человек в минуту`. The cell does not say which meaning was intended.
