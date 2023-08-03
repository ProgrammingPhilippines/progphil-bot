--
--depends: 0_initial_migrations

CREATE TABLE IF NOT EXISTS pph_auto_responder_channels (
    id SERIAL PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    response_id BIGINT NOT NULL,

    FOREIGN KEY (response_id) REFERENCES pph_auto_responses(id) ON DELETE CASCADE ON UPDATE CASCADE
);

ALTER TABLE pph_auto_responses ADD COLUMN IF NOT EXISTS specified BOOLEAN NOT NULL DEFAULT FALSE;