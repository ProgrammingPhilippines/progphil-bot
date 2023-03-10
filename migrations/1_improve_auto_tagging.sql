--
--depends: 0_initial_migrations

ALTER TABLE IF EXISTS pph_helpers RENAME TO pph_auto_tag;
ALTER TABLE IF EXISTS pph_auto_tag
    ADD COLUMN IF NOT EXISTS tag_in BIGINT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS msg VARCHAR(4000) DEFAULT 'Calling out peeps!\n\n';