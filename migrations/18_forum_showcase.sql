CREATE TYPE IF NOT EXISTS forum_showcase_interval AS ENUM ('daily', 'weekly', 'monthly');
CREATE TYPE IF NOT EXISTS forum_showcase_status AS ENUM ('active', 'inactive');

CREATE TABLE IF NOT EXISTS forum_showcase (
    id INTEGER UNIQUE PRIMARY KEY,
    target_channel INTEGER NOT NULL,
    schedule TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    interval forum_showcase_interval NOT NULL DEFAULT 'daily',
    showcase_status forum_showcase_status NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
);

CREATE TABLE IF NOT EXISTS forum_showcase_forum (
    forum_id INTEGER UNIQUE PRIMARY KEY,
    showcase_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
);

ALTER TABLE forum_showcase_forum ADD FOREIGN KEY (showcase_id) REFERENCES forum_showcase(id) ON DELETE CASCADE;

INSERT INTO pph_config_auto(config_type) VALUES ('forum_showcase');
INSERT INTO forum_showcase(
    id,
    target_channel,
) VALUES (
    1,
    0,
);