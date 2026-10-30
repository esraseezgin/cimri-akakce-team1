# Validation results

18 of 18 checks passed.

| Check | Result | Detail |
|---|---|---|
| 24 store files exist and match the 24 catalog stores | PASS | 24 files |
| all CSV and Markdown files are valid UTF-8 and keep Turkish letters | PASS | 77,857 names with Turkish letters |
| record counts equal the cleaned source; raw = records + rejected + duplicates + unreadable | PASS | 99,375 records |
| source files unchanged (clean.csv, offers.csv, price history; raw 01_Food in git) | PASS | 72 files checked |
| offer_id values equal the catalog, are unique, and every missing one is a reported conflict | PASS | 127 records without offer_id |
| original names and prices kept exactly | PASS | 0 differences |
| no word, number, promotion or model code lost in standard names | PASS | 0 rows |
| all 24 store files have the same columns | PASS | 26 columns |
| records under one product_id agree on brand, size, unit, pack, variant, model, capacity and colour, one record per store | PASS | 53,753 product_ids |
| no product_id joins prices more than 3x apart (false-merge guard) | PASS | 0 groups |
| every product_id shows one canonical_product_name in all stores | PASS | 8,626 multi-store groups checked |
| no clean record keeps glued sizes, repeated size letters or a stray lower-case letter | PASS | 0 rows |
| products_master has each product_id once and matches the store files | PASS | 53,753 rows |
| product_matches lists every record once; unmatched_products holds every record without product_id | PASS | 99,375 matches, 28,153 unmatched |
| every rejected row and removed exact duplicate is reported | PASS | 56 rows |
| no record with a blocking problem is marked clean | PASS | 0 records |
| product_ids are the same on every rerun (with the saved registry, and from scratch) | PASS |  |
| decisions written in the Excel book survive a rerun | PASS |  |
