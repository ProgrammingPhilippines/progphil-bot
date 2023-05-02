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

CREATE TABLE IF NOT EXISTS pph_forum_cleanup_message (
	c_trigger VARCHAR(5) UNIQUE,
	c_message VARCHAR(4000)
);

INSERT INTO pph_config_auto(config_type) VALUES ('forum_cleanup');