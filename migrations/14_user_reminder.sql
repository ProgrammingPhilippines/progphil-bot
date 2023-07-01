INSERT INTO pph_config_auto(config_type) VALUES ('user_reminder');

CREATE TABLE IF NOT EXISTS pph_user_reminder(
    message TEXT NOT NULL
);