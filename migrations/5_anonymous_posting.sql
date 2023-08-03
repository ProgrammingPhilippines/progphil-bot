--
--depends: 2_create_configs

CREATE TABLE IF NOT EXISTS pph_anonymous_posting_forums (
    forum_id BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS pph_anonymous_posting_log_channel (
    channel_id BIGINT PRIMARY KEY
);

INSERT INTO pph_config_auto(config_type) VALUES ('anonymous_posting');