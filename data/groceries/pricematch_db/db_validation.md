# Database export validation

12 of 12 checks passed. Schema: `001_initial_schema.sql` from isah-ismail/PriceMatch, plus `002_pricematch_grocery_import.sql`.

PostgreSQL was not available on the build machine. The schema was translated to SQLite and every row was inserted with foreign keys on, so NOT NULL, CHECK, UNIQUE and FOREIGN KEY were enforced by a database engine; types SQLite does not enforce were checked separately.

| Check | Result | Detail |
|---|---|---|
| all export files are valid UTF-8 | PASS |  |
| each table file has exactly the schema's columns in order (offers + source_offer_key from 002) | PASS |  |
| schema 001 + 002: every row loads with NOT NULL, CHECK, UNIQUE and foreign keys enforced | PASS | categories 419; brands 2,114; products 81,181; retailers 24; offers 98,645; price_history 98,645 |
| no foreign key points to a missing row | PASS | 0 problems |
| schema 001 alone rejects exactly the offers without a product URL (why 002 is needed) | PASS | 80,492 offers rejected, 80,492 have no URL |
| lengths, NUMERIC(12,2), integers, timestamps and ids fit PostgreSQL types | PASS |  |
| every clean record with an offer_id is loaded once; every other record is in excluded_records.csv | PASS | 98,645 loaded + 730 excluded = 99,375 |
| price, store and original name of every offer equal the delivery | PASS | 0 differences |
| offers share a database product only when they share a product_id in the delivery | PASS |  |
| price_history has the scraped price of every offer on its scrape date | PASS |  |
| every category has a name; unclassified products sit in one 'Sınıflandırılmamış' category | PASS | 419 categories |
| rebuilding gives byte-identical files (ids are stable) | PASS |  |
