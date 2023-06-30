CREATE TABLE IF NOT EXISTS pph_settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value BIGINT
);

CREATE TABLE IF NOT EXISTS pph_welcomer (
    message_id INTEGER PRIMARY KEY,
    message VARCHAR(2000)
);