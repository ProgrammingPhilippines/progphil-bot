-- depends: 21_add_enable_accept_solutions
-- depends: 12_dev_help_tag
-- depends: add_enable_mark_as_solved

CREATE TABLE IF NOT EXISTS pph_post_assist_mark_as_solved_tags (
    forum_id BIGINT PRIMARY KEY,
    tag_id BIGINT NOT NULL
);

INSERT INTO pph_post_assist_mark_as_solved_tags (forum_id, tag_id)
SELECT pac.forum_id, dhs.tag_id
FROM pph_post_assist_config pac
JOIN dev_help_solved dhs ON dhs.id = 1
WHERE pac.enable_mark_as_solved = true
  AND dhs.tag_id IS NOT NULL
ON CONFLICT (forum_id) DO NOTHING;
