CREATE TABLE IF NOT EXISTS pph_anonymous_posting_forums (
    forum_id BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS pph_anonymous_posting_posts (
    post_uuid uuid PRIMARY KEY,
    post_id BIGINT,
    post_author BIGINT,
    post_title VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS pph_anonymous_posting_log_channel (
    channel_id BIGINT PRIMARY KEY
);

INSERT INTO pph_config_auto(config_type) VALUES ('anonymous_posting');