-- depends: 18_post_assist
ALTER TABLE pph_post_assist_config
ADD COLUMN IF NOT EXISTS enable_accept_solutions BOOLEAN DEFAULT FALSE;

CREATE TABLE
    IF NOT EXISTS pph_post_assist_config_accept_solutions (
        id SERIAL PRIMARY KEY,
        thread_id BIGINT NOT NULL,
        post_assist_config_id SERIAL NOT NULL,
        user_id BIGINT NOT NULL,
        message_id BIGINT NOT NULL,
        FOREIGN KEY (post_assist_config_id) REFERENCES pph_post_assist_config (id) ON DELETE CASCADE
    );

ALTER TABLE pph_post_assist_config_accept_solutions
ADD COLUMN IF NOT EXISTS message_id BIGINT NOT NULL;