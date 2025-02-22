ALTER TABLE `pph_post_assist_config`
ADD COLUMN IF NOT EXISTS `enable_accept_solutions` BOOLEAN DEFAULT FALSE;

CREATE TABLE
    IF NOT EXISTS `pph_post_assist_config_accept_solutions` (
        `id` INT (11) NOT NULL AUTO_INCREMENT,
        `thread_id` INT (11) NOT NULL,
        `post_assist_config_id` INT (11) NOT NULL,
        `user_id` INT (11) NOT NULL,
        `created_at` DATETIME NOT NULL,
    );