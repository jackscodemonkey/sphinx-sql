-- Function: schema1.fn_function_name()

-- DROP FUNCTION schema1.fn_function_name();

CREATE OR REPLACE FUNCTION schema1.fn_function() RETURNS void
    AS $BODY$
/*
Parameters:
Name | Type | Description

Return: Void
Purpose:
Detailed explanation of the function which includes:
        - Function business logic
        - Transformation rules
        - Here is a bit more text.
Dependent Objects:
    Type    |Name
    Table   |schema_name.source_table5
    View    |schema_name.target_table6
ChangeLog:
    Date   |     Author      |    Ticket | Modification
	YYYY-MM-DD |	Developer name |	T-223 | Short Modification details or some really long text that will continue on.
*/
DECLARE
    v_source_rec_cnt BIGINT;
    v_fstart_ts TIMESTAMP;
    v_fend_ts TIMESTAMP;
    BEGIN
        SELECT 1;
    END;
LANGUAGE pgpgsql;