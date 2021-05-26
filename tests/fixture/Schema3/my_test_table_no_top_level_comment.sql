CREATE TABLE IF NOT EXISTS my_test_schema.my_test_table_no_top_level_comment (
    name character varying,
    value smallint,
    weight numeric(5,2)
    object_owner varchar(100),
) DISTRIBUTED BY (name, value)
PARTITION BY (object_owner)
;

COMMENT ON COLUMN my_test_schema.my_test_table_no_top_level_comment.name IS 'This field contains the name.';
COMMENT ON COLUMN my_test_schema.my_test_table_no_top_level_comment.weight IS 'This field contains the weight with two decimal places.';
