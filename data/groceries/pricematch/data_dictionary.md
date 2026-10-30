# Data dictionary: PriceMatch grocery data (Team 1, cleaning and preprocessing)

Source: the daily price files of the inflation study (`InflationResearchStudy/InflationItems/Datas/01_Food/<Store>/`), newest file per store; 24 supermarkets. All files are UTF-8, comma-separated, with a header row. Empty means "not known": no value is ever guessed.

## stores/<Store>.csv: one file per store, same 26 columns

| Column | Type | Meaning | Empty when |
|---|---|---|---|
| `retailer` | text | Store name as in the source folder (e.g. `Migros`, `Tarım Kredi Kooperatif`) | never |
| `offer_id` | text | Permanent ID of this store's listing, e.g. `IDEAL-000123`. Given once by the store catalog, never recomputed from the name; reused on every later scrape. | the store lists the same name twice with different prices on that day (no ID until resolved) |
| `record_key` | text | Unique key of the row: `retailer\|source_file\|source_row`. Use it when `offer_id` is empty. | never |
| `product_id` | text | Cross-store product identity, e.g. `PRD-000123`. Same physical product (same brand, words, quantity, pack, variant) = same `product_id` in every store. Identifies the product, not a price. | identity not certain; see `match_status` |
| `original_product_name` | text | Product name exactly as scraped (after whitespace/HTML cleanup) | never |
| `standardized_product_name` | text | `Brand – Product name – Quantity` for this store's listing; Turkish casing fixed, units written one way, abbreviations opened only when unambiguous | never |
| `canonical_product_name` | text | One display name shared by every store record of the same `product_id` (the most used standardized form; ties: fewer words in capitals, more Turkish letters). Equals `standardized_product_name` when there is no `product_id`. | never |
| `brand` | text | Brand, only when confirmed (brand list; ambiguous words such as "Bizim" only with evidence from a store's own brand column). One spelling per brand across stores. | brand not confirmed |
| `model` | text | Model or article code from the name (e.g. `32PHS6009/62`) | no code in the name; ALL-CAPS names are not searched |
| `category` | text | TÜİK 2026 CPI item code (7 digits), only when it is valid and agrees with `category_number` | code missing or inconsistent in the source |
| `category_number` | text | CPI main group as scraped (`01` food … `13` personal care; `0` = not in the basket) | source has no category columns (Migros, SozSanal) |
| `sub_category_number` | text | CPI item code as scraped, unchanged | as above |
| `variant` | text | Variant words in the name, fixed order: fat level, `laktozsuz`, `organik`, flavour (`çilekli`, `bitter` …) | none in the name |
| `capacity` | text | Storage / battery capacity: `128 GB`, `5000 mAh` | none in the name |
| `size` | text | Net quantity as written in the name, one form: `500 g`, `1,5 kg`, `330 ml`, `1 L`, `4 x 70 g` (4 items of 70 g), `20'li` (20 pieces), `40'lı, 200 g`, `2 x 430 g + 380 g`, `200 ml (koli X27)` (case size written in the name). Decimal comma. | name has no quantity, or the product is sold by `kg` / `adet` |
| `color` | text | Colour words for non-food products (CPI groups 03, 05, 08), same for every store of one `product_id` | none, or food product |
| `pack_quantity` | integer | Number of items in the pack (`4` for `4 x 70 g`, `20` for `20'li`) | single item or unknown |
| `unit` | text | Sales unit: `paket` (sold as the package in `size`), `kg` (price per kilo), `adet` (price per piece) | no quantity and no sales unit in the name |
| `price` | decimal | Shelf price in Turkish lira (TRY), dot as decimal separator, as scraped | never |
| `data_quality_status` | text | `clean`, or `needs_review` when the source cannot settle the row (see `review_reason`) | never |
| `match_status` | text | `matched` (same `product_id` in 2+ stores), `single_retailer` (certain identity, sold by one store), `ambiguous` (same key but not certain: two listings in one store, or prices more than 3x apart), `not_matchable` (no brand, no quantity, needs review or no `offer_id`) | never |
| `review_reason` | text | Codes separated by `; `. Blocking (row is `needs_review`): `placeholder_price` (999/9999), `suspicious_size`, `corrupted_size_text` (two different numbers glued to the size in the source, e.g. `115 Gr125 gr`; kept as written), `case_or_single_price_unclear` (price may be for the case), `same_name_different_price_no_offer_id`. Information only: `ambiguous_brand_word_not_used`, `brand_not_found_in_name`, `promotion_text_kept_in_name`, `letter_case_uncertain`, `abbreviation_not_expanded`, `no_quantity_in_name`, `range_kept_in_name` (e.g. diaper `9-14 kg`, egg `63-72 g`: a range, not the size) | no remark |
| `standardization_changes` | text | What the name standardization changed (in Turkish): `miktar ayrı yazıldı`, `yazım: Avakado → Avokado`, `kısaltma: Org. → Organik`, … | nothing changed |
| `scrape_date` | date | Date of the source file, `YYYY-MM-DD` | never |
| `source_file`, `source_row` | text, integer | Source file and its data row (1 = first row after the header) | never |

## products_master.csv: one row per product_id (no prices)

`product_id`, `canonical_product_name`, `brand`, `model`, `variant`, `capacity`, `size`, `color`, `pack_quantity`, `unit`, `category`, `retailer_count`, `offer_count`, `retailers`, `match_rule` (`name` or `model`), `match_signature` (the exact key; also the ID registry).

## product_matches.csv: every store record

`retailer`, `offer_id`, `record_key`, `product_id`, `canonical_product_name`, `match_status`, `match_reason`.

## unmatched_products.csv: records without a product_id

`retailer`, `offer_id`, `record_key`, `original_product_name`, `standardized_product_name`, `price`, `data_quality_status`, `match_status`, `reason`.

## rejected_records.csv: rows removed during cleaning

`retailer`, `source_file`, `source_row`, `original_value`, `reason`: `rejected_invalid_price` (0, negative or unreadable), `rejected_missing_name`, `exact_duplicate_of_row_<n>` (same name and same price as row n of the same file).

## data_quality_stats.csv: per-store counts behind data_quality_report.md

## ID rules

- **`offer_id`**: Store prefix and a sequence number. It is found again on the next scrape by a normalized name key (letters, Turkish characters and size spelling unified; word order ignored) or an approved alias. A renamed listing is never given a new ID automatically: it is held for review.
- **`product_id`**: Given only when a record is `clean`, has an `offer_id`, a confirmed brand and a quantity (or `kg`/`adet` unit). Records share one only when brand, every word of the product name, quantity and sales unit are equal (or brand + model code + capacity + quantity for coded products).
  - `500 g` vs `1 kg`, single vs multipack, different flavour, colour or model never share an ID.
  - No barcodes are used: none of the 24 current files has one (only A101's files before 26 Oct 2026 had a barcode column).
  - IDs are kept in `products_master.csv` and reused on every run. New identities get the next number in sorted order, so the same input always gives the same IDs.
  - If a name fix changes a key, the records keep the product_id they had before, as long as that ID is not in use by another key.
