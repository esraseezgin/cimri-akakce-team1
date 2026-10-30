# Grocery data for the PriceMatch database

Team 1's cleaned grocery data, shaped for the PriceMatch schema (`isah-ismail/PriceMatch`,
`Database & Backend Development Team/database/migrations/001_initial_schema.sql`). One CSV per table, columns in
schema order, ids already set so every foreign key lines up.

## Load it

Use a new, empty test database first, never a database that already holds data.

1. Apply migrations `000_migration_tracking.sql` and `001_initial_schema.sql` with the official migration runner.
2. Add `002_pricematch_grocery_import.sql` to `database/migrations/` and apply it. It is required; see below.
3. Optionally add `003_grocery_import_safety.sql` after 002. It also rejects a blank `source_offer_key`. Our data has none, so the load does not depend on it.
4. From this folder, load the data:
   `psql -d pricematch_db -v ON_ERROR_STOP=1 -f load_pricematch.sql`
5. Check the load:
   `psql -d pricematch_db -v ON_ERROR_STOP=1 -f verify_pricematch_import.sql`

   It stops with an error if any of these is wrong: row counts (24 retailers, 81,181 products, 98,645 offers and initial history rows, 419 categories, 2,114 brands), a duplicated `source_offer_key`, an offer without its product or retailer, or an offer whose first history price differs from `current_price`. The counts belong to this export: update them if the files are rebuilt from newer data.

`load_pricematch.sql` runs in one transaction, so on any error nothing is loaded. It loads all six tables through staging tables (`INSERT … OVERRIDING SYSTEM VALUE`, because the ids are identity columns). At the end it moves every identity past the loaded ids, so rows added later get new ids. Migrations 001 and 002 should not be edited after they are applied; later changes go in new numbered migrations, like 003.

## Why migration 002

| Change | Reason |
|---|---|
| `offers.product_url` may be NULL | 19 of the 24 stores have no product link in their daily files. Inventing links would be wrong. The CHECK against blank strings and `UNIQUE (retailer_id, product_url)` still hold for every URL given. Umut's data README asks for the same change. |
| `offers.source_offer_key VARCHAR(30) UNIQUE` | Team 1's permanent listing id (e.g. `IDEAL-000123`). Daily prices arrive with this key, so new `price_history` rows can be attached to the right offer. |

Without 002, schema 001 rejects exactly the 80,492 offers that have no URL; everything else loads.

## What is in the files

| Table | Rows | Source |
|---|---:|---|
| `retailers` | 24 | Store names; `website_url` from each store's own scraper code in the inflation study (`retailer_sources.csv`) |
| `categories` | 419 | TÜİK 2026 CPI hierarchy (main group → … → 7-digit item), Turkish names from the inflation study's `tuik_cpi_categories_comma.csv`, only the codes in use and their parents, plus one `Sınıflandırılmamış` (unclassified) category |
| `brands` | 2,114 | Confirmed brands, one spelling each |
| `products` | 81,181 | Team 1's cross-store `product_id` proposal: 8,625 products sold by 2+ stores; every unmatched offer is its own product. `name` is the canonical standardized name (`Brand – Product – Quantity`). |
| `offers` | 98,645 | One per store listing: original store name, price as scraped (TRY), `last_updated` = scrape date |
| `price_history` | 98,645 | The scraped price of each offer on its scrape date |

From Umut's spec files (team repo `data/specs/`), joined by the exact product name (Hakmar, Ideal, Marketzade,
Sariyer, HappyCenter):

| Field | Filled |
|---|---|
| `product_url` | 18,153 offers |
| `retailer_product_id` | 18,169 offers |
| `image_url` | 16,798 products |
| `barcode` | 4,191 products |

Safety rules for these fields:
- A barcode is used only with a valid check digit and when it belongs to one product. 299 shared barcodes were left empty: they come from reused images.
- A URL is used only when it points to one offer. 16 shared URLs were left empty.

## What is not loaded or left empty, and why

- `excluded_records.csv`: 730 records that are not `clean` (999 prices, case-vs-single price, corrupted size text, same name with two prices) or have no `offer_id`. Their price or identity is not certain.
- `products.category_id` is the unclassified category for 19,407 products: the source has no valid CPI code for them.
- `offers.in_stock` is NULL: the sources do not say.
- `last_updated` and `recorded_at` are the scrape date at 00:00 Istanbul time: the sources give a date, not a time.

## Mapping files

- `id_map_offers.csv`: `source_offer_key` → database `offer_id`.
- `id_map_products.csv`: database `product_id` → Team 1 `product_id` (`PRD-…`), or the single offer it holds.

The matching team can re-link offers with `UPDATE offers SET product_id = …`. No other table depends on the product grouping.

## Checked

`db_validation.md` lists the checks (12 of 12 passed). PostgreSQL was not available on the build machine, so the schema was translated to SQLite and every row was inserted with foreign keys on. That enforced NOT NULL, CHECK, UNIQUE and FOREIGN KEY. Lengths, NUMERIC(12,2), timestamps and ids were checked separately.

The numbers `verify_pricematch_import.sql` expects were recomputed from these files and all match. The PostgreSQL-only parts (`\copy`, `OVERRIDING SYSTEM VALUE`, `setval`, the verify script itself) still need their first run on PostgreSQL 17 (steps 1–5 above). Passing them shows the data loaded completely and consistently. It does not prove that every cross-store product grouping is right: that review belongs to the matching team.

## Files

| File | Purpose |
|---|---|
| `categories.csv`, `brands.csv`, `products.csv`, `retailers.csv`, `offers.csv`, `price_history.csv` | the six tables |
| `002_pricematch_grocery_import.sql` | required migration |
| `003_grocery_import_safety.sql` | optional migration |
| `load_pricematch.sql` | loads the six tables |
| `verify_pricematch_import.sql` | checks the load on PostgreSQL |
| `id_map_offers.csv`, `id_map_products.csv` | Team 1 ids ↔ database ids |
| `excluded_records.csv` | the 730 records not loaded, with reasons |
| `retailer_sources.csv` | where each retailer's web address was taken from |
| `db_validation.md` | test results |
