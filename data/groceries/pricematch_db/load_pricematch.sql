-- Load Team 1's grocery data into an empty PriceMatch database.
--
-- Needs migrations 000, 001 and 002_pricematch_grocery_import.sql applied first.
-- Run from this folder (the \copy paths are relative):
--     psql -d pricematch_db -v ON_ERROR_STOP=1 -f load_pricematch.sql
-- Everything runs in one transaction: on any error nothing is loaded.
--
-- The ids in the CSV files are given here so the foreign keys line up. The id columns are
-- GENERATED ALWAYS AS IDENTITY, so the rows go through staging tables and
-- INSERT ... OVERRIDING SYSTEM VALUE, and each identity is moved past the loaded ids at the end.

BEGIN;

CREATE TEMP TABLE stg_categories (category_id BIGINT, parent_category_id BIGINT, name TEXT);
CREATE TEMP TABLE stg_brands (brand_id BIGINT, name TEXT);
CREATE TEMP TABLE stg_products (product_id BIGINT, category_id BIGINT, brand_id BIGINT, name TEXT, barcode TEXT,
                                model TEXT, variant TEXT, image_url TEXT);
CREATE TEMP TABLE stg_retailers (retailer_id BIGINT, name TEXT, website_url TEXT);
CREATE TEMP TABLE stg_offers (offer_id BIGINT, product_id BIGINT, retailer_id BIGINT, retailer_product_id TEXT,
                              retailer_product_name TEXT, product_url TEXT, current_price NUMERIC(12,2),
                              currency TEXT, in_stock BOOLEAN, last_updated TIMESTAMPTZ, source_offer_key TEXT);
CREATE TEMP TABLE stg_price_history (history_id BIGINT, offer_id BIGINT, price NUMERIC(12,2), recorded_at TIMESTAMPTZ);

\copy stg_categories FROM 'categories.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy stg_brands FROM 'brands.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy stg_products FROM 'products.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy stg_retailers FROM 'retailers.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy stg_offers FROM 'offers.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy stg_price_history FROM 'price_history.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')

INSERT INTO categories (category_id, parent_category_id, name) OVERRIDING SYSTEM VALUE
    SELECT category_id, parent_category_id, name FROM stg_categories ORDER BY category_id;

INSERT INTO brands (brand_id, name) OVERRIDING SYSTEM VALUE
    SELECT brand_id, name FROM stg_brands ORDER BY brand_id;

INSERT INTO products (product_id, category_id, brand_id, name, barcode, model, variant, image_url) OVERRIDING SYSTEM VALUE
    SELECT product_id, category_id, brand_id, name, barcode, model, variant, image_url FROM stg_products ORDER BY product_id;

INSERT INTO retailers (retailer_id, name, website_url) OVERRIDING SYSTEM VALUE
    SELECT retailer_id, name, website_url FROM stg_retailers ORDER BY retailer_id;

INSERT INTO offers (offer_id, product_id, retailer_id, retailer_product_id, retailer_product_name, product_url,
                    current_price, currency, in_stock, last_updated, source_offer_key) OVERRIDING SYSTEM VALUE
    SELECT offer_id, product_id, retailer_id, retailer_product_id, retailer_product_name, product_url,
           current_price, currency, in_stock, last_updated, source_offer_key FROM stg_offers ORDER BY offer_id;

INSERT INTO price_history (history_id, offer_id, price, recorded_at) OVERRIDING SYSTEM VALUE
    SELECT history_id, offer_id, price, recorded_at FROM stg_price_history ORDER BY history_id;

-- New rows added later get ids after the loaded ones.
SELECT setval(pg_get_serial_sequence('categories', 'category_id'), (SELECT MAX(category_id) FROM categories));
SELECT setval(pg_get_serial_sequence('brands', 'brand_id'), (SELECT MAX(brand_id) FROM brands));
SELECT setval(pg_get_serial_sequence('products', 'product_id'), (SELECT MAX(product_id) FROM products));
SELECT setval(pg_get_serial_sequence('retailers', 'retailer_id'), (SELECT MAX(retailer_id) FROM retailers));
SELECT setval(pg_get_serial_sequence('offers', 'offer_id'), (SELECT MAX(offer_id) FROM offers));
SELECT setval(pg_get_serial_sequence('price_history', 'history_id'), (SELECT MAX(history_id) FROM price_history));

COMMIT;
