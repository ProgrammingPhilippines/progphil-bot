--
--depends: 19_thread_showcase

CREATE TYPE forum_showcase_weekday AS ENUM ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday');
ALTER TABLE IF EXISTS pph_forum_showcase ADD COLUMN IF NOT EXISTS weekday forum_showcase_weekday NOT NULL DEFAULT 'monday';