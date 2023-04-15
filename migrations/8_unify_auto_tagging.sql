DROP TABLE pph_auto_tag_messages;

ALTER TABLE pph_auto_tag ADD COLUMN c_message VARCHAR(4000) DEFAULT 'Calling out peeps!';
ALTER TABLE pph_auto_tag RENAME COLUMN tag_in to forum_id;
ALTER TABLE pph_auto_tag ADD UNIQUE (forum_id);