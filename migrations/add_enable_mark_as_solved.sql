-- depends: 18_post_assist
ALTER TABLE pph_post_assist_config
ADD COLUMN IF NOT EXISTS enable_mark_as_solved BOOLEAN DEFAULT FALSE;