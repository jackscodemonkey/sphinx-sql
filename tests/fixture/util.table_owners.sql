/*
Purpose:
Stores table owners
*/
CREATE TABLE util.table_owners (
    table_schema character varying,
    table_name character varying,
    object_owner character varying
) DISTRIBUTED BY (table_schema, table_name)
PARTITION BY (object_owner);
