CREATE TABLE IF NOT EXISTs pph_post_assist_config (
    id SERIAL PRIMARY KEY,
    forum_id BIGINT
);

CREATE TABLE IF NOT EXISTS pph_post_assist_reply (
    id SERIAL PRIMARY KEY,
    custom_message VARCHAR(4000),
    configuration_id INTEGER,

    FOREIGN KEY (configuration_id)
        REFERENCES pph_post_assist_config(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pph_post_assist_tag_message (
    id SERIAL PRIMARY KEY,
    custom_message VARCHAR(500),
    configuration_id INTEGER,

    FOREIGN KEY (configuration_id)
        REFERENCES pph_post_assist_config(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pph_post_assist_tags (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(6),
    entity_id BIGINT,

    configuration_id INTEGER,

    FOREIGN KEY (configuration_id)
        REFERENCES pph_post_assist_config (id)
        ON DELETE CASCADE
);