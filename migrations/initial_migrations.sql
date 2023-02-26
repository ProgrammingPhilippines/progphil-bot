CREATE TABLE IF NOT EXISTS pph_auto_responses (
    id SERIAL PRIMARY KEY,
    message VARCHAR(40),
    response VARCHAR(4000),
    response_type CHAR(7)
);

CREATE TABLE IF NOT EXISTS pph_trivia(
  channel_id BIGINT,
  schedule VARCHAR(5)
);

CREATE TABLE IF NOT EXISTS pph_helpers(
    id SERIAL PRIMARY KEY,
    obj_id BIGINT,
    obj_type VARCHAR(10)
);