# Groceries: cleaned product catalog

`build_grocery_catalog.py` reads every daily CSV the inflation study saved for its 24 supermarkets (`InflationResearchStudy/InflationItems/Datas/01_Food`, Feb–Oct 2026, 2,003 files, 10.3 million rows) and writes **one row per store product** to `data/groceries/grocery_products.csv`: 183,875 products, 99,348 of them in each store's latest scrape.

The daily prices stay in the inflation study's repo. This file is the "collect product information once" side; it keeps the latest, lowest and highest price so the shop can sort cheap to expensive without the full history.

## Run it

```bash
python scrapers/groceries/build_grocery_catalog.py          # ~4 min, standard library only
python scrapers/groceries/build_grocery_catalog.py --datas "D:/path/to/InflationItems/Datas"
```

By default it looks for `Desktop/InflationResearchStudy` next to this repo, like `beymen_specs.py`. Running it again rebuilds both files from scratch.

## What it cleans

| Problem in the daily files | What the script does |
| --- | --- |
| 15+ header spellings (`product_name`, `ad`, `isim`, `Ürün Adı`, `price (TL)`, `fiyat`, `product_price`, …), `;` instead of `,`, files with no header row | Reads them all with one alias list |
| Dates in file names as `2026-10-29`, `2026_10_29`, `29.10.2026`, or month-day only (Kim: `products9-5.csv`) | Reads them all; month-day files are taken as 2026 |
| Prices as `"34,99 TL"`, `₺419,90`, `1.769` (thousands dot) | Converted to a number in TL |
| HTML entities, odd dashes and quotes, double spaces in names | Cleaned; `name_key` is a lower-case ASCII version for matching |
| Same product scraped twice on one day | Kept once (lowest price of the day) |
| Brand only inside the name | Taken from the store's brand column when there is one (A101, Macrocenter, Onur), else from the start of the name using a 4,139-brand list (from the ucuzu project) |
| Size written as `1 L`, `1lt`, `1000 ml`, `1.480 Ml`, `6x200 ml`, `3'lü 240 cc`, `kg` | Size per item in g / ml / adet, plus pack count; loose produce sold per kg is marked `sold_by = kg` |
| Different pack sizes are hard to compare | `unit_price_tl` in TL/kg, TL/L or TL/adet |
| Variants that make two products different | `fat` (tam / yarım / az yağlı, yağsız), `lactose_free`, `organic`, `flavour` |

## Columns of `grocery_products.csv`

| Column | Example | Notes |
| --- | --- | --- |
| retailer | Migros | Store folder name in the inflation study |
| retailer_product_id, barcode, product_url | 26004112 | Only where the store's scraper ever saved them (see table below) |
| product_name | Pınar Yarım Yağlı Süt 1 L | Newest spelling |
| name_key | pinar yarim yagli sut 1 l | For matching |
| brand | Pınar | |
| size_value, size_unit, pack_count, sold_by | 1000, ml, , pack | |
| fat, lactose_free, organic, flavour | yarım yağlı, , , | Empty when not in the name |
| price_latest_tl, unit_price_tl, unit_price_unit | 74.95, 74.95, TL/L | |
| price_min_tl, price_max_tl | 59.90, 79.50 | Over all days seen, placeholder prices (999, 9999) excluded |
| first_seen, last_seen, days_seen | 2026-03-13, 2026-10-29, 120 | |
| category_number, sub_category_number | 01, 0114101 | TÜİK codes when the store sent them; empty otherwise |
| status | ok / review | `review` = brand or size missing, or a price that looks wrong |
| issues | size_not_found;no_store_product_id | Semicolon-separated |

Issue codes: `brand_not_found`, `size_not_found`, `price_placeholder_suspect` (999 / 9999), `price_range_suspect` (highest price over 5× the lowest), `tufe_item_missing`, `not_in_latest_scrape` (the store no longer lists it), `no_store_product_id`.

## Coverage per store

| Retailer | Dates | Products | In latest scrape | Brand | Size | Store id | URL |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A101 | 03-13 – 10-29 | 10,364 | 8,564 | 94% | 80% | 87% | 87% |
| Arden | 03-02 – 10-29 | 8,501 | 6,771 | 79% | 90% | 0% | 88% |
| Basdas | 02-21 – 10-29 | 3,552 | 2,729 | 84% | 96% | 0% | 0% |
| Baskent | 02-24 – 10-29 | 382 | 93 | 12% | 98% | 0% | 0% |
| BizimMarket | 03-14 – 10-29 | 3,087 | 1,578 | 84% | 93% | 68% | 0% |
| Cagri | 03-01 – 10-29 | 8,690 | 7,088 | 84% | 93% | 89% | 89% |
| CarrefourSA | 02-23 – 10-29 | 17,277 | 4,980 | 78% | 85% | 0% | 0% |
| Gurmar | 02-21 – 10-29 | 9,086 | 3,434 | 82% | 84% | 73% | 51% |
| Hakmar | 10-17 – 10-27 | 1,230 | 1,177 | 65% | 99% | 0% | 0% |
| Hapeloglu | 02-24 – 10-29 | 8,407 | 5,042 | 85% | 91% | 88% | 88% |
| HappyCenter | 03-04 – 10-27 | 9,017 | 5,841 | 80% | 91% | 0% | 0% |
| Ideal | 02-20 – 10-29 | 3,094 | 2,717 | 86% | 92% | 0% | 0% |
| Kale | 03-01 – 10-29 | 5,530 | 2,838 | 85% | 94% | 0% | 0% |
| Kim | 02-23 – 10-29 | 3,535 | 2,146 | 80% | 89% | 0% | 0% |
| Macrocenter | 02-20 – 10-29 | 15,396 | 7,800 | 94% | 81% | 80% | 0% |
| Marketzade | 02-24 – 10-29 | 7,601 | 2,802 | 85% | 93% | 0% | 0% |
| Migros | 02-24 – 10-25 | 19,793 | 3,025 | 74% | 65% | 0% | 0% |
| Mopas | 03-02 – 10-29 | 7,433 | 5,600 | 87% | 100% | 0% | 0% |
| Onur | 02-18 – 10-29 | 1,526 | 345 | 92% | 95% | 0% | 0% |
| Sariyer | 02-26 – 10-29 | 9,529 | 6,259 | 81% | 86% | 0% | 0% |
| SozSanal | 02-26 – 03-31 | 5,164 | 4,945 | 82% | 92% | 0% | 0% |
| Tarım Kredi Kooperatif | 03-01 – 10-29 | 3,991 | 2,729 | 59% | 15% | 0% | 0% |
| sehzade | 02-27 – 10-29 | 18,117 | 9,238 | 66% | 76% | 0% | 0% |
| sok_market | 02-22 – 10-27 | 3,573 | 1,607 | 58% | 82% | 0% | 0% |
| **Total** | | **183,875** | **99,348** | 80% | 83% | 25% | 20% |

Store ids and URLs come only from older files: on 2026-10-26 the inflation study cut most grocery scrapers to 4 columns (name, price, two TÜİK codes), so newer products have neither.

## Known limits

- **Products are not matched across stores here.** `name_key`, brand, size and variant are the inputs for Team 02; the same milk is still written differently by each store ("Pınar Süt 1 L", "PINAR SUT UHT 1LT").
- A product renamed by its store becomes a second row (old row flagged `not_in_latest_scrape`).
- Some names carry no size at all (Tarım Kredi: "ABANT SU"); nothing can be extracted there.
- Store-own brands (Baskent, sehzade, Tarım Kredi) are often missing from the brand list.
- A container's capacity is read as a size ("Su Bardağı 380 cc" is a glass, not 380 ml of something), so its unit price is meaningless.
- Some non-food items sold in supermarkets are included (toothpaste, toys); their TÜİK group, when present, is in `category_number`.
