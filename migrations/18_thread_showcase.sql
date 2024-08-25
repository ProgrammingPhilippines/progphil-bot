--
--depends: 2_create_configs
DROP TYPE IF EXISTS forum_showcase_interval;
DROP TYPE IF EXISTS forum_showcase_status;

CREATE TYPE forum_showcase_interval AS ENUM ('daily', 'weekly', 'monthly');
CREATE TYPE forum_showcase_status AS ENUM ('active', 'inactive');

CREATE TABLE IF NOT EXISTS pph_forum_showcase (
    id SERIAL PRIMARY KEY,
    target_channel BIGINT NOT NULL,
    schedule TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    interval forum_showcase_interval NOT NULL DEFAULT 'daily',
    showcase_status forum_showcase_status NOT NULL DEFAULT 'inactive',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pph_forum_showcase_forum (
    forum_id BIGINT PRIMARY KEY,
    showcase_id SERIAL NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (showcase_id)
        REFERENCES pph_forum_showcase(id)
        ON DELETE CASCADE
);

INSERT INTO pph_config_auto(config_type) VALUES ('forum_showcase');
INSERT INTO pph_forum_showcase(
    id,
    target_channel
) VALUES (
    1,
    0
);