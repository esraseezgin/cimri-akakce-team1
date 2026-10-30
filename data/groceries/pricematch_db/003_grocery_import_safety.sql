-- Optional migration following migration 002.
-- Prevent empty source IDs; when a source ID exists, it remains globally unique.
-- PostgreSQL 17 compatible. Requires 002 to have been applied first.
ALTER TABLE offers
    ADD CONSTRAINT offers_source_offer_key_nonblank
    CHECK (source_offer_key IS NULL OR LENGTH(BTRIM(source_offer_key)) > 0);
