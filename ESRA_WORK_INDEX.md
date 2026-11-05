# Esra's work in this repository

This repository is Esra and Umut's working repository. This page shows where Esra's work is. Files with a dependency stay where they are. Files with no dependency are in [archive_esra_old_work/](archive_esra_old_work/README.md).

## Week 1 (current)

| Item | Location |
|---|---|
| Handoff guide | [README_ESRA_WEEK1.md](README_ESRA_WEEK1.md) |
| Data dictionary draft | [DATA_DICTIONARY.md](DATA_DICTIONARY.md) |
| Required-field checklist draft | [REQUIRED_FIELD_CHECKLIST.md](REQUIRED_FIELD_CHECKLIST.md) |
| Audit report and outputs | [data/audit/](data/audit/week1_audit_report.md) |
| Audit script | [scrapers/audit/build_week1_audit.py](scrapers/audit/build_week1_audit.py) |

The "Esra — Cleaning" section of [WEEK1_SUMMARY.md](WEEK1_SUMMARY.md) points to the same evidence.

## Earlier work kept in place

| Item | Location | Why it stays |
|---|---|---|
| Grocery catalog | [pricematch_cleaned_all_markets.csv](data/groceries/pricematch/pricematch_cleaned_all_markets.csv) | Umut's `brands.py` and `catalog.py` read this path |
| Store files with prices | `data/groceries/pricematch/stores/` | Week 1 audit input |
| Quality results | [data_quality_report.md](data/groceries/pricematch/data_quality_report.md), `data_quality_stats.csv`, `rejected_records.csv` | Week 1 evidence |
| Grocery rules | [data_dictionary.md](data/groceries/pricematch/data_dictionary.md) | Referenced by `DATA_DICTIONARY.md` |
| Cleaned spec files | [data/specs_clean/](data/specs_clean/README.md) | Week 1 audit input; named in Umut's `RETAILER_SHORTLIST.md` |
| PostgreSQL export | [data/groceries/pricematch_db/](data/groceries/pricematch_db/README.md) | Named in Umut's section of `WEEK1_SUMMARY.md` |

`data/specs_clean/` was built before the latest changes to `data/specs/`.

## Archived

| Item | Location |
|---|---|
| Cross-store `product_id` proposal | [matching_groundwork/](archive_esra_old_work/README.md) |
| 2026-10-30 grocery delivery reports | [grocery_reports/](archive_esra_old_work/README.md) |
| Test file and older local attempts | [archive_esra_old_work/](archive_esra_old_work/README.md) |

## What goes to the team repository

Only the Week 1 files listed in [README_ESRA_WEEK1.md](README_ESRA_WEEK1.md). The earlier work stays here.
