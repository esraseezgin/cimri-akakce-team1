# Data-quality report: PriceMatch grocery data

24 supermarkets, newest daily file per store (scrape dates 2026-03-31 … 2026-10-29). All numbers come from `data_quality_stats.csv`.

## 1. Audit: rows, missing values, duplicates

| | Rows |
|---|---:|
| Raw rows in the 24 source files | 99,431 |
| Unreadable rows (wrong number of columns) | 0 |
| Rejected: price 0, negative or unreadable, or no name (`rejected_records.csv`) | 37 |
| Exact duplicates removed: same name and price in one file (`rejected_records.csv`) | 19 |
| **Records delivered** | **99,375** |
| `clean` | 98,645 |
| `needs_review` | 730 |

Same name with a different price in one store is **not** treated as a duplicate (it can be another size or variant); those rows are kept and marked.

Missing values in the delivered records:

| Field | Missing | Why |
|---|---:|---|
| `offer_id` | 127 | same name, different price on one day; kept, not merged |
| `brand` | 19,965 | not in the brand list, or an ambiguous word without evidence; never guessed |
| `size` and `unit` | 12,064 | the name gives no quantity (fresh and non-food goods, Tarım Kredi names) |
| `category` (valid CPI item) | 26,723 | source code missing, `0`, or inconsistent (Basdas, CarrefourSA, Gurmar; no columns in Migros, SozSanal) |

## 2. Standardization

- Names rewritten as `Brand – Product name – Quantity`: 96,719 of 99,375; the original name is kept in `original_product_name`.
- Units in one form (`g`, `kg`, `ml`, `L`, count words `'li` with correct Turkish vowel harmony, `yaprak`, `kapsül`, `tablet`, `poşet`), decimal comma, 1000 ml → 1 L, 1000 g → 1 kg, cl → ml.
- Turkish casing and letters fixed (`Içim` → `İçim`; ALL-CAPS words take the spelling used by other stores, else stay as written and are marked). Technical abbreviations and model codes kept (`HD`, `LED`, `USB-C`, `32PHS6009/62`). One spelling per brand across stores.
- Abbreviations opened only when the meaning is certain (`Org.` → `Organik`; `Çik.` only from the next word).
- An automatic check confirms that no word, number, promotion or model code of the original name is lost.
- Sizes glued twice by the source (`182 Gr182 gr`, `400 Gr0 gr`) are written once; conflicting ones (`115 Gr125 gr`) are kept and marked. Repeated size letters (`Hasta Bezi L L`) are written once.
- Every record of one `product_id` carries the same `canonical_product_name`; each store's own `standardized_product_name` and `original_product_name` stay.

## 3. Extracted attributes

| Attribute | Records |
|---|---:|
| brand | 79,410 |
| size or sales unit | 87,311 |
| pack quantity | 5,498 |
| variant (fat, lactose-free, organic, flavour) | 11,165 |
| model code | 722 |
| capacity (GB, TB, mAh) | 29 |
| colour (non-food groups) | 655 |

## 4. Price and required-field validation

| Code | Records | Meaning |
|---|---:|---|
| `abbreviation_not_expanded` | 56 | abbreviation with two meanings kept |
| `ambiguous_brand_word_not_used` | 1,125 | brand-like word without evidence, kept in the name |
| `brand_not_found_in_name` | 107 | brand list entry not found in the name; brand left empty |
| `case_or_single_price_unclear` | 479 | price may be for a case, not one item (blocking) |
| `corrupted_size_text` | 15 | two different numbers glued to the size in the source, e.g. `115 Gr125 gr` (blocking) |
| `letter_case_uncertain` | 1,757 | ALL-CAPS word kept as written |
| `no_quantity_in_name` | 12,064 | no quantity in the name |
| `placeholder_price` | 87 | price 999 / 9999, may be a placeholder (blocking) |
| `promotion_text_kept_in_name` | 109 | promotion such as `5 + 2` kept in the name |
| `range_kept_in_name` | 142 | usage or grade range kept in the name, not the size |
| `same_name_different_price_no_offer_id` | 127 | same name, different price in one store (blocking) |
| `suspicious_size` | 22 | size below 1 or above 50,000 g/ml (blocking) |

Required fields (`product_name`, `price`) are present in every delivered record; prices are positive numbers. Rows that failed were rejected and listed in `rejected_records.csv`.

## 5. Cross-store identity (`product_id`)

| | Records |
|---|---:|
| `matched` (same product in 2+ stores) | 26,095 |
| `single_retailer` (certain identity, one store) | 45,127 |
| `ambiguous` | 264 |
| `not_matchable` | 27,889 |

53,753 product_ids; 8,626 of them are sold by 2 or more stores (up to 18).

Why records have no product_id:

| Reason | Records |
|---|---:|
| no reliable brand | 19,863 |
| no quantity in name | 7,296 |
| needs_review | 730 |
| same key | 258 |
| same key held by several records of one store | 6 |

## Per store

| Store | Date | Records | Clean | Needs review | No brand | No size/unit | Matched | Single | Not matchable |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A101 | 2026-10-29 | 8,565 | 8,482 | 83 | 672 | 1,250 | 1,080 | 5,700 | 1,749 |
| Arden | 2026-10-29 | 6,771 | 6,737 | 34 | 1,352 | 327 | 2,169 | 2,973 | 1,609 |
| Basdas | 2026-10-29 | 2,729 | 2,720 | 9 | 483 | 33 | 1,329 | 874 | 519 |
| Baskent | 2026-10-29 | 93 | 93 | 0 | 91 | 5 | 0 | 2 | 91 |
| BizimMarket | 2026-10-29 | 1,578 | 1,361 | 217 | 236 | 86 | 369 | 695 | 496 |
| Cagri | 2026-10-29 | 7,088 | 7,073 | 15 | 1,148 | 394 | 2,411 | 3,200 | 1,458 |
| CarrefourSA | 2026-10-29 | 4,986 | 4,966 | 20 | 1,310 | 244 | 1,523 | 1,966 | 1,480 |
| Gurmar | 2026-10-29 | 3,435 | 3,423 | 12 | 638 | 138 | 1,274 | 1,385 | 764 |
| Hakmar | 2026-10-27 | 1,177 | 1,172 | 5 | 437 | 12 | 367 | 360 | 447 |
| Hapeloglu | 2026-10-29 | 5,042 | 5,032 | 10 | 771 | 427 | 1,482 | 2,466 | 1,084 |
| HappyCenter | 2026-10-27 | 5,856 | 5,809 | 47 | 1,290 | 231 | 1,703 | 2,723 | 1,410 |
| Ideal | 2026-10-29 | 2,717 | 2,689 | 28 | 427 | 157 | 918 | 1,262 | 525 |
| Kale | 2026-10-29 | 2,838 | 2,832 | 6 | 491 | 50 | 1,172 | 1,142 | 517 |
| Kim | 2026-10-29 | 2,146 | 2,137 | 9 | 476 | 186 | 672 | 878 | 589 |
| Macrocenter | 2026-10-29 | 7,801 | 7,783 | 18 | 838 | 1,582 | 2,045 | 3,470 | 2,271 |
| Marketzade | 2026-10-29 | 2,802 | 2,797 | 5 | 577 | 213 | 846 | 1,187 | 762 |
| Migros | 2026-10-25 | 3,025 | 3,015 | 10 | 459 | 53 | 1,422 | 1,101 | 494 |
| Mopas | 2026-10-29 | 5,600 | 5,596 | 4 | 755 | 0 | 5 | 4,836 | 759 |
| Onur | 2026-10-29 | 345 | 326 | 19 | 15 | 17 | 17 | 282 | 46 |
| Sariyer | 2026-10-29 | 6,259 | 6,228 | 31 | 1,514 | 1,120 | 2,304 | 2,047 | 1,888 |
| SozSanal | 2026-03-31 | 4,946 | 4,929 | 17 | 955 | 398 | 1,251 | 2,435 | 1,250 |
| Tarım Kredi Kooperatif | 2026-10-29 | 2,731 | 2,705 | 26 | 1,133 | 2,297 | 55 | 214 | 2,457 |
| sehzade | 2026-10-29 | 9,238 | 9,136 | 102 | 3,320 | 2,837 | 1,227 | 3,362 | 4,642 |
| sok_market | 2026-10-27 | 1,607 | 1,604 | 3 | 577 | 7 | 454 | 567 | 582 |

Note: SozSanal's newest file is from 2026-03-31; the other stores are from 2026-10-17 … 2026-10-29.
