--
--depends: 19_thread_showcase

CREATE TYPE forum_showcase_weekday AS ENUM ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday');

ALTER TABLE IF EXISTS pph_forum_showcase ADD COLUMN weekday forum_showcase_weekday NOT NULL DEFAULT 'Monday';
