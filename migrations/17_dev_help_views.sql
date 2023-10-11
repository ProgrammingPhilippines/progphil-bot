--
--depends: 2_create_configs


CREATE TABLE IF NOT EXISTS pph_dev_help_views (
    thread_id BIGINT PRIMARY KEY,
    message_id BIGINT,
    author_id BIGINT,
    closed BOOLEAN DEFAULT false
);

INSERT INTO pph_config_auto(config_type) VALUES ('dev_help');