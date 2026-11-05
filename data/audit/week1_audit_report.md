# Week 1 dataset audit (Team 1, data cleaning)

This report adds the parts of the Week 1 audit that were not yet in the repository: the raw field list, the comparison of retailer schemas, and a quality audit of the electronics data. The grocery audit stays in `data/groceries/pricematch/data_quality_report.md`. Umut's `DATA_AUDIT_BEYMEN_POZITIF.md` covers the two MVP stores in more detail.

**Data used**

- 24 grocery stores: the same raw daily files the grocery catalog was built from (dates 2026-03-31 to 2026-10-29).
- 3 electronics stores: the 2026-10-29 daily files of Beymen, Pozitif and Samsung.
- 8 spec files in `data/specs/`, as of commit `670d457`.
- `data/specs_clean/` for the cleaned electronics results.

No source file was changed. Numbers are a snapshot; rebuild them with `scrapers/audit/build_week1_audit.py`.

| File | Contents |
|---|---|
| `field_inventory.csv` | One row per store and field: inferred type, missing count and %, distinct values, example |
| `schema_summary.csv` | One row per store: columns, schema group, required columns, price formats, duplicates |
| `electronics_quality_stats.csv` | Every electronics check, per store |
| `summary.json` | The same results in one machine-readable file |

## 1. Main findings

1. **Seven different schemas exist.** 22 of 24 grocery stores share one 4-column format. Migros and SozSanal have only `product_name` and `price`.
2. **Grocery daily files have no store product ID and no URL.** Spec files fill that gap for only 5 of the 24 grocery stores.
3. **No source has a dedicated `description` column.** The plan lists descriptions as a field to collect. `DATA_AUDIT_BEYMEN_POZITIF.md` confirms there are none for the two MVP stores. For the other stores, `attributes` (raw site data as JSON, in spec files) was not checked for description text.
4. **`category` means different things.** It is a store's own category in daily and spec files, but the 7-digit CPI code in our catalog (section 3).
5. **Sub-category codes are not always 7 digits.** Basdas, CarrefourSA, Gurmar and Kale have shorter codes, so they are not valid CPI item codes as written.
6. **Beymen's spec data is thin.** 89.2% of rows have no brand in the spec file, 73.0% no model code, and all have no image. Cleaning lowered missing brands to 6,638 (50.5%).
7. **Pozitif and Samsung have no CPI code in `data/specs_clean/`,** even though the daily files have it for 1,316 and 273 joined rows. It can be added by joining on the store product ID.
8. **Pozitif has 130 daily rows with price 0.** All 130 are bundles (`is_bundle = True`), so they should not count as a real lowest price.
9. **A repeated name and price is not a duplicate in electronics.** Beymen 956 and Samsung 81 such rows all have different store IDs. No ID repeats in any daily file.

## 2. Raw fields

### Grocery daily files

| Field | Type | Stores | Notes |
|---|---|---:|---|
| `product_name` | text | 24 | Never empty |
| `price` | decimal | 24 | Dot decimal in 23 stores; decimal comma in SozSanal, so its type reads as text |
| `category_number` | integer | 22 | Missing in Migros and SozSanal; written `1` or `01` depending on the store |
| `sub_category_number` | integer | 22 | Missing in Migros and SozSanal; `0` = not in the CPI basket (10,459 rows) |

All 99,431 raw rows parse with the right number of columns. No name or price cell is empty.

### Electronics daily files

| Store | Extra columns after the 4 required ones | Store ID |
|---|---|---|
| Beymen | `UrunID` | `UrunID` |
| Pozitif | `category`, `regular_price`, `sku`, `product_id`, `in_stock`, `is_outlet`, `categories`, `url` | `product_id` |
| Samsung | `id`, `category` | `id` |

Types and missing values for every column are in `field_inventory.csv`.

## 3. Schema comparison

| Group | Source | Stores | Columns | Shape |
|---|---|---:|---:|---|
| S01 | Daily | 22 grocery | 4 | The 4 required columns |
| S02 | Daily | Migros, SozSanal | 2 | `product_name`, `price` |
| S03 | Daily | Beymen | 5 | S01 + `UrunID` |
| S04 | Daily | Pozitif | 12 | S01 + 8 extra columns |
| S05 | Daily | Samsung | 6 | S01 + `id`, `category` |
| S06 | Spec | Beymen, Pozitif, Samsung | 21 | Electronics attributes; no price |
| S07 | Spec | Hakmar, HappyCenter, Ideal, Marketzade, Sariyer | 18 | Grocery attributes with catalog links; no price |

### Same concept, different column names

| Concept | Daily | Spec file | Cleaned catalog |
|---|---|---|---|
| Product name | `product_name` | `name` | `original_product_name`, `standardized_product_name` |
| Store's product ID | `UrunID`, `product_id`, `id`; none for groceries | `retailer_product_id` | `retailer_product_id` (specs_clean only) |
| Team 1 listing ID | none | `catalog_offer_id` (S07) | `offer_id` |
| Price | `price`; also `regular_price` in Pozitif | none | `price` in `stores/*.csv` only |
| CPI item code | `sub_category_number` | `tuik_code` (S07) | `category`, `sub_category_number` |
| Store's own category | `category`, `categories` | `category` | `store_category` (specs_clean only) |
| Link | `url` (Pozitif only) | `url` | `product_url` (specs_clean only) |
| Image | none | `image_url` | `image_url` (specs_clean only) |
| Barcode | none | `barcode` (S07) | `barcode` (specs_clean only) |
| Description | none | none (see finding 3) | none |

### Format differences

| Issue | Stores | Rows |
|---|---|---:|
| Decimal comma in price | SozSanal | 4,984 |
| Price 0 | SozSanal 37; Pozitif 130 (bundles) | 167 |
| `sub_category_number` shorter than 7 digits, not `0` | CarrefourSA 4,535; Basdas 2,080; Gurmar 1,492; Kale 187 | 8,294 |
| No category columns | Migros, SozSanal | 8,009 |
| Newest file older than 2026-10-29 | SozSanal 03-31; Migros 10-25; Hakmar, HappyCenter, sok_market 10-27 | 5 stores |

Two more points for anyone reading the raw files:

- HTML entities appear in raw Pozitif names (`&#8211;`).
- A simple comparison of raw text finds 12 repeated rows in the grocery files, while the cleaning step removed 19. The cleaning step compares names after whitespace and HTML cleanup, which finds more.

## 4. Electronics quality

### Spec files

| Check | Beymen | Pozitif | Samsung |
|---|---:|---:|---:|
| Rows | 13,144 | 1,334 | 1,389 |
| Empty name or store ID | 0 | 0 | 0 |
| Repeated store ID | 0 | 0 | 0 |
| Rows repeating an earlier name | 1,120 | 1 | 607 |
| Model code used by 2+ store IDs | 244 | 47 | 0 |
| Invalid storage, RAM or screen number | 0 | 0 | 0 |
| Invalid link or date | 0 | 0 | 0 |
| Not new (display or used) | 0 | 86 | 0 |
| Bundles | 0 | 130 | 14 |

Rows repeating a name are expected: they are often colour or storage variants that the name does not show. Keep them apart by store ID, colour and storage.

### Missing values in spec files

| Field | Beymen | Pozitif | Samsung |
|---|---:|---:|---:|
| `brand` | 11,728 (89.2%) | 11 (0.8%) | 0 |
| `model_code` | 9,589 (73.0%) | 0 | 0 |
| `color` | 7,661 (58.3%) | 271 (20.3%) | 245 (17.6%) |
| `storage_gb` | 12,316 (93.7%) | 806 (60.4%) | 938 (67.5%) |
| `ram_gb` | 12,647 (96.2%) | 1,194 (89.5%) | 1,389 (100%) |
| `screen_size_in` | 12,273 (93.4%) | 996 (74.7%) | 1,155 (83.2%) |
| `url` | 0 | 0 | 0 |
| `image_url` | 13,144 (100%) | 0 | 0 |

Many of these are not faults: a cable has no storage or screen size. They should not be read as data loss.

### After cleaning (`data/specs_clean/`)

| Check | Beymen | Pozitif | Samsung |
|---|---:|---:|---:|
| Rows kept | 13,144 | 1,334 | 1,389 |
| `needs_review` | 90 | 12 | 32 |
| No brand | 6,638 | 9 | 0 |
| No CPI category | 4,513 | 1,334 | 1,389 |

### Daily prices (2026-10-29)

| Check | Beymen | Pozitif | Samsung |
|---|---:|---:|---:|
| Rows | 11,207 | 1,333 | 366 |
| Empty price | 0 | 0 | 0 |
| Price 0 or unreadable | 0 | 130 | 0 |
| Joined to the spec file by store ID | 11,188 (99.8%) | 1,333 (100%) | 361 (98.6%) |

## 5. Recommended next steps

- Add the CPI code to Pozitif and Samsung in `data/specs_clean/` from the daily files.
- Exclude bundles with price 0 from lowest-price queries (Team 3).
- Agree one name per concept with Teams 2 and 3, especially `category`.
- Check `attributes` in the other stores for description text if descriptions are needed beyond the MVP stores.
- Decide how to treat the shorter sub-category codes: leave empty or ask the scraper owners to fix them. Their owners are in the inflation study.
