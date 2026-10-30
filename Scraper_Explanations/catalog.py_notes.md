**How catalog.py connects our spec files to Esra's catalog**

catalog.py (Data Collection & Processing Team/scrapers/specs/catalog.py) fills our grocery spec files with Esra's cleaning work, from data/groceries/pricematch/pricematch_cleaned_all_markets.csv.

**Why two sources**

They describe the same store listings, but each has what the other lacks:

| | Our spec files | Esra's catalog |
|---|---|---|
| Stores | 5 grocery stores | 24 grocery stores |
| Store's real product id, link, image | yes | no |
| Barcode | Hakmar, Marketzade, HappyCenter | no |
| Clean size, unit, variant, TÜİK category, quality check | no | yes |

**How the rows are linked**

Esra's `original_product_name` is the name exactly as the daily file writes it, and so is our `name`. So the same listing has the same name in both:

Our file:  Hakmar | Arı Mama Sütlü Pirinç Unu 500 Gr | id 13853 | barcode 8696540190015

Her file:  Hakmar | Arı Mama Sütlü Pirinç Unu 500 Gr | HAKMAR-001175 | 500 g | paket | 0111211 | clean

When a name appears **exactly once** for that store in her catalog, our row takes her offer_id (as `catalog_offer_id`), brand, TÜİK code (as `tuik_code`), size, unit, pack_quantity, variant and data_quality_status. 94–98% of our rows are found.

If the name is not in her catalog (a product that appeared after her snapshot) or appears twice, the row keeps our own brand and the size as written in the name, and `catalog_offer_id` stays empty. Nothing is guessed.

**It runs on every scrape**

Each grocery script calls catalog.enrich() just before saving, so the next run does not undo it. When Esra updates her catalog, the next run picks up her changes.

See [[groceries_overview_notes]] and, for the one brand spelling, [[brands.py_notes]].
