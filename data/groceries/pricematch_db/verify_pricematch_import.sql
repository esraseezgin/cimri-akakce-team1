-- Run after load_pricematch.sql on a dedicated PriceMatch grocery database.
-- Fail loudly if imports have wrong counts or broken links.
DO $$
DECLARE
  n_categories BIGINT;
  n_brands BIGINT;
  n_products BIGINT;
  n_retailers BIGINT;
  n_offers BIGINT;
  n_history BIGINT;
  n_duplicate_keys BIGINT;
  n_dangling BIGINT;
  n_price_diff BIGINT;
BEGIN
  SELECT COUNT(*) INTO n_categories FROM categories;
  SELECT COUNT(*) INTO n_brands FROM brands;
  SELECT COUNT(*) INTO n_products FROM products;
  SELECT COUNT(*) INTO n_retailers FROM retailers;
  SELECT COUNT(*) INTO n_offers FROM offers;
  SELECT COUNT(*) INTO n_history FROM price_history;

  IF (n_categories,n_brands,n_products,n_retailers,n_offers,n_history)
     IS DISTINCT FROM (419::bigint,2114::bigint,81181::bigint,24::bigint,98645::bigint,98645::bigint) THEN
    RAISE EXCEPTION 'Wrong counts: categories %, brands %, products %, retailers %, offers %, history %',
      n_categories,n_brands,n_products,n_retailers,n_offers,n_history;
  END IF;

  SELECT COUNT(*) INTO n_duplicate_keys
  FROM (SELECT source_offer_key FROM offers WHERE source_offer_key IS NOT NULL
        GROUP BY source_offer_key HAVING COUNT(*) > 1) dup;
  IF n_duplicate_keys > 0 THEN RAISE EXCEPTION 'Duplicated source_offer_key: %',n_duplicate_keys; END IF;

  SELECT COUNT(*) INTO n_dangling
  FROM offers o LEFT JOIN products p ON p.product_id=o.product_id
    LEFT JOIN retailers r ON r.retailer_id=o.retailer_id
  WHERE p.product_id IS NULL OR r.retailer_id IS NULL;
  IF n_dangling > 0 THEN RAISE EXCEPTION 'Unlinked offers: %',n_dangling; END IF;

  SELECT COUNT(*) INTO n_price_diff
  FROM offers o LEFT JOIN price_history h ON h.offer_id=o.offer_id
  WHERE h.history_id IS NULL OR h.price<>o.current_price;
  IF n_price_diff > 0 THEN RAISE EXCEPTION 'Missing/differing initial history: %',n_price_diff; END IF;

  RAISE NOTICE 'PASS: 24 retailers, 81,181 products, 98,645 offers & initial history entries.';
END $$;
