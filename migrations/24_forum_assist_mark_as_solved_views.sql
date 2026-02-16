-- depends: 23_forum_assist_mark_as_solved_tags
-- depends: 17_dev_help_views

CREATE TABLE IF NOT EXISTS pph_post_assist_mark_as_solved_views (
    thread_id BIGINT PRIMARY KEY,
    message_id BIGINT NOT NULL,
    author_id BIGINT NOT NULL,
    closed BOOLEAN DEFAULT false
);

INSERT INTO pph_post_assist_mark_as_solved_views (
    thread_id,
    message_id,
    author_id,
    closed
)
SELECT thread_id, message_id, author_id, closed
FROM pph_dev_help_views
ON CONFLICT (thread_id) DO NOTHING;
