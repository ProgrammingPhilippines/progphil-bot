INSERT INTO pph_config_auto(config_type) VALUES ('user_reminder');

CREATE TABLE IF NOT EXISTS pph_user_reminder(
    id INTEGER NOT NULL PRIMARY KEY,
    message TEXT NOT NULL
);