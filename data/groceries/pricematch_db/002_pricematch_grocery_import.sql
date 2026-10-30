-- PriceMatch Database
-- Migration 002: grocery data import from Team 1 (data cleaning and preprocessing)
--
-- 1. Most grocery stores give no product link in their daily price files (19 of 24 stores).
--    A listing is identified by its store and its key, not by its URL, so product_url may be empty.
--    The existing CHECK (LENGTH(TRIM(product_url)) > 0) still rejects blank strings, and
--    UNIQUE (retailer_id, product_url) still applies to every URL that is given.
-- 2. source_offer_key keeps Team 1's permanent listing id (e.g. IDEAL-000123). Daily prices
--    arrive with this key, so price_history rows can be added to the right offer.

ALTER TABLE offers ALTER COLUMN product_url DROP NOT NULL;

ALTER TABLE offers ADD COLUMN source_offer_key VARCHAR(30);

ALTER TABLE offers ADD CONSTRAINT offers_source_offer_key_key UNIQUE (source_offer_key);
