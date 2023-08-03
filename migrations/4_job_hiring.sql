--
--depends: 2_create_configs

CREATE TABLE IF NOT EXISTS pph_job_hiring (
    channel_id BIGINT,
    schedule VARCHAR(70),
    schedule_type INTEGER
);

INSERT INTO pph_config_auto(config_type) VALUES ('job_hiring');