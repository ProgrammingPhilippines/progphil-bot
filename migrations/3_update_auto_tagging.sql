ALTER TABLE pph_auto_tag DROP COLUMN msg;

CREATE TABLE IF NOT EXISTS pph_auto_tag_messages(
    id SERIAL PRIMARY KEY,
    forum_id BIGINT,
    msg VARCHAR(200)
);