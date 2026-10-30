# Final report: Team 1 data cleaning and preprocessing (PriceMatch)

Prepared by Esra (Team 1, Data Cleaning & Preprocessing).

## Task checklist

| Task | Status | Where |
|---|---|---|
| 1. Audit fields, missing values, duplicates, formats, units | Done | `data_quality_report.md` §1, `data_quality_stats.csv` |
| 2. Standardize names, casing, whitespace, punctuation, units; keep originals | Done | `stores/*.csv` (`original_product_name` kept), report §2 |
| 3. Extract brand, model, capacity, size, colour, pack quantity | Done where the name allows; nothing guessed | `stores/*.csv`, report §3 |
| 4. Validate prices and required fields; report incomplete or rejected records | Done | report §4, `rejected_records.csv`, `review_reason` |
| 5. Data dictionary, clean dataset, data-quality statistics | Done | `data_dictionary.md`, `stores/`, `data_quality_report.md` |
| Extra: cross-store `product_id` | Done (separate files) | `products_master.csv`, `product_matches.csv`, `unmatched_products.csv` |

## Results

- Records: 99,375 from 24 stores; `clean` 98,645, `needs_review` 730.
- Rejected rows: 37; exact duplicates removed: 19.
- product_ids: 53,753; 8,626 are sold by 2+ stores. Records matched across stores: 26,095; single-store: 45,127; without product_id: 28,153 (ambiguous 264, not matchable 27,889).
- Validation: 18 of 18 checks passed. Details: `validation_results.md`.

## Limitations

- One snapshot per store (newest daily file). SozSanal's newest file is from March 2026.
- product_ids are deliberately strict: brand + every name word + quantity must agree. Stores that word the same product differently stay separate (no false merges, but some true matches are missed). Records without a confirmed brand or quantity get no product_id.
- No barcodes are available in the current files, so matching is name-based.
- 730 records need review (case-vs-single price, 999 prices, suspicious or corrupted sizes, same name with two prices); their values are kept exactly as scraped.

## Files

`stores/` (24 CSV), `products_master.csv`, `product_matches.csv`, `unmatched_products.csv`, `rejected_records.csv`, `data_quality_stats.csv`, `data_dictionary.md`, `data_quality_report.md`, `validation_results.md`, `FINAL_REPORT.md`. All UTF-8, comma-separated.

## GitHub delivery (team repo `esraseezgin/cimri-akakce-team1`)

Add only this folder's contents, as `data/groceries/pricematch/` in the team repo. Do not add: the raw inflation-study data, the store catalog and its test replays, Excel review books, backups, scripts (they use helper files that were removed from the repo on purpose), or anything under `cleaned_data/`.

In Windows PowerShell:

```powershell
cd C:\Users\esra\Desktop\cimri-akakce-team1
git status
git pull --rebase origin main
New-Item -ItemType Directory -Force data\groceries\pricematch
Copy-Item -Recurse -Force C:\Users\esra\Desktop\groceries_review\naming\final\* data\groceries\pricematch\
git add data/groceries/pricematch
git diff --cached --name-only
git commit -m "Add cleaned, standardized grocery data for 24 stores with product IDs"
git push origin main
```

Before `git commit`, the list from `git diff --cached --name-only` must contain only paths under `data/groceries/pricematch/` (33 files). Never use `git add .` or `--force`. If the push is rejected, run `git pull --rebase origin main` again and push.
