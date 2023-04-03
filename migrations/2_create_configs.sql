CREATE TABLE IF NOT EXISTS pph_config_auto (
    config_type VARCHAR(30) PRIMARY KEY,
    config_status BOOLEAN DEFAULT true
);

INSERT INTO pph_config_auto(config_type)
SELECT 'auto_responder'
    WHERE NOT EXISTS
        (SELECT 1 FROM pph_config_auto WHERE config_type = 'auto_responder');

INSERT INTO pph_config_auto(config_type)
SELECT 'auto_tagging'
    WHERE NOT EXISTS
        (SELECT 1 FROM pph_config_auto WHERE config_type = 'auto_tagging');

INSERT INTO pph_config_auto(config_type)
SELECT 'job_hiring'
    WHERE NOT EXISTS
        (SELECT 1 FROM pph_config_auto WHERE config_type = 'job_hiring');