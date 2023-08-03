--
--depends: 2_create_configs

INSERT INTO pph_config_auto(config_type) VALUES ('user_reminder');

CREATE TABLE IF NOT EXISTS pph_user_reminder (
    id INTEGER PRIMARY KEY,
    message TEXT,
    day INT,
    interval INT,
    member_role BIGINT,
    visitor_role BIGINT
);
