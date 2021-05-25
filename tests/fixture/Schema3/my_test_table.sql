/*
Purpose:
This a new table to show how auto documentation can add new objects quickly.
Attributes and Comments on Columns can also be parsed.
Dependent Objects:
    Type    |Name
    Schema   |my_test_schema
ChangeLog:
	Date    |    Author    |    Ticket    |    Modification
	2020-12-26    |  Developer_2  |   T-232    |    Add Comment On Columns
	2020-10-26    |  Developer_2  |   T-220    |    Initial Definition
*/
CREATE TABLE IF NOT EXISTS my_test_schema.my_test_table (
    name character varying,
    value smallint,
    weight numeric(5,2)
    object_owner varchar(100),
) DISTRIBUTED BY (name, value)
PARTITION BY (object_owner)
;

COMMENT ON COLUMN my_test_schema.my_test_table.name IS 'This field contains the name.';
COMMENT ON COLUMN my_test_schema.my_test_table.weight IS 'This field contains the weight with two decimal places.';
