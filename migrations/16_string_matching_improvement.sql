alter table pph_auto_responses
add IF NOT EXISTS matching_type varchar(255) default 'lenient' not null;
