CREATE TABLE IF NOT EXISTS dev_help_solved (
    id INT PRIMARY KEY,
    tag_id BIGINT,
    custom_message VARCHAR(2000),
    reminder_message VARCHAR(2000)
);