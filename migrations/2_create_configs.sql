CREATE TABLE IF NOT EXISTS pph_config_auto (
    config_type VARCHAR(30) PRIMARY KEY,
    config_status BOOLEAN DEFAULT true
);

INSERT INTO pph_config_auto(config_type) VALUES ('auto_responder');
INSERT INTO pph_config_auto(config_type) VALUES ('auto_tagging');