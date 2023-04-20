CREATE TABLE IF NOT EXISTS pph_forum_cleanup_forums (
	forum_id BIGINT
);

CREATE TABLE IF NOT EXISTS pph_forum_cleanup_sched (
    id INTEGER UNIQUE,
	duration_unit VARCHAR(4)
);

CREATE TABLE IF NOT EXISTS pph_forum_cleanup_conf (
    conf_type VARCHAR(5) UNIQUE,
    num_days INTEGER
);

INSERT INTO pph_config_auto(config_type) VALUES ('forum_cleanup');