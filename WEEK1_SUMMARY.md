# Week 1 summary — Team 01 (Data collection & processing)

Umut (scraping), Esra (cleaning). This page lists where each Week 1 task from the
8-week plan is answered.

## Umut — Scraping

| Task | Where |
|---|---|
| Shared GitHub access | Done: the whole team has access to this repo |
| List the stores and categories | [README.md](README.md): "Where the data comes from" and "What is done" |
| Look at the existing scripts | [Scraper_Explanations/](Scraper_Explanations/): one note per scraper |
| Pick two stores | [RETAILER_SHORTLIST.md](RETAILER_SHORTLIST.md): **Beymen and Pozitif** |
| What each store gives (IDs, links, descriptions) | [README.md](README.md) store table, [scrapers/specs/README.md](scrapers/specs/README.md) |
| How often prices update | [RETAILER_SHORTLIST.md](RETAILER_SHORTLIST.md): "How often prices update" (daily) |

## Esra — Cleaning

| Task | Where |
|---|---|
| Load sample files, list columns and types | [data/groceries/pricematch/data_dictionary.md](data/groceries/pricematch/data_dictionary.md) |
| Missing values, duplicates, formats | [data/groceries/pricematch/data_quality_report.md](data/groceries/pricematch/data_quality_report.md), [data_quality_stats.csv](data/groceries/pricematch/data_quality_stats.csv) |
| Compare the stores' formats | [data/groceries/pricematch/data_quality_report.md](data/groceries/pricematch/data_quality_report.md) |
| Data dictionary | Groceries: [data_dictionary.md](data/groceries/pricematch/data_dictionary.md). Electronics: [scrapers/specs/README.md](scrapers/specs/README.md), [data/specs_clean/README.md](data/specs_clean/README.md) |

## Dataset audit for the MVP stores

[DATA_AUDIT_BEYMEN_POZITIF.md](DATA_AUDIT_BEYMEN_POZITIF.md): column coverage, problems found
and rules for the other teams. Main points:

- **147 products** can be compared at both stores today (203 shared model codes).
- Beymen has **no images**, and its brand and model code come only from product names.
- Pozitif has **130 bundles with price 0** and display/used products that share the new
  product's model code. These must be filtered out.

## Beyond Week 1 (already done)

- Spec files for 8 stores (3 electronics, 5 grocery): `data/specs/`
- Esra's cleaned catalog of 24 grocery stores and name-based cross-store matching:
  `data/groceries/pricematch/`
- Cleaned spec files: `data/specs_clean/`
- Database import files for the PostgreSQL schema: `data/groceries/pricematch_db/`
