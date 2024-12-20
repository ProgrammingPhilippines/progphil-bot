--
--depends: 2_create_configs
DROP TYPE IF EXISTS forum_showcase_interval;

CREATE TYPE forum_showcase_interval AS ENUM ('daily', 'weekly', 'monthly');

CREATE TABLE IF NOT EXISTS pph_forum_showcase (
    id SERIAL PRIMARY KEY,
    target_channel BIGINT NOT NULL,
    schedule TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    interval forum_showcase_interval NOT NULL DEFAULT 'weekly',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pph_forum_showcase_forum (
    id SERIAL PRIMARY KEY,
    forum_id BIGINT,
    showcase_id SERIAL NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (showcase_id)
        REFERENCES pph_forum_showcase(id)
        ON DELETE CASCADE
);

INSERT INTO pph_config_auto(config_type, config_status) VALUES ('forum_showcase', false);
INSERT INTO pph_forum_showcase(
    id,
    target_channel
) VALUES (
    1,
    0
);
