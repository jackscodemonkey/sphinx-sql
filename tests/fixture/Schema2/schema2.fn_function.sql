CREATE OR REPLACE FUNCTION schema2.fn_function (p_id bigint)
    RETURNS VOID
    AS $BODY$
/*
Parameters:
Name | Type | Description
p_id | bigint | Id of target record.

Return: Void
Purpose:
    - Detailed explanation of the function which includes:
    - Function: business logic
    - Transformation rules
Dependent Objects:
    Type    |Name
    Table   |schema_name.source_table2
    View    |schema1.my_view
ChangeLog:
    Date   |     Author      | Ticket | Modification
	2020-10-23 | Developer Name | T-123 | Test documentation of functions
    2020-11-23 | Developer Name | T-124 | Updates to fix bugs in T-123
*/
BEGIN
    SELECT
        TRUE;
END;
$BODY$
LANGUAGE plpgsql;

