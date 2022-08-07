CREATE OR REPLACE PROCEDURE schema2.fn_proceedure (p_bigint bigint)
    AS $BODY$
/*
Parameters:
Name | Type | Description
p_id | bigint | Id of target record.

Return: Void
Purpose:
    - Detailed explanation of the procedure which includes:
    - Procedure: business logic
    - Transformation rules
Dependent Objects:
    Type    |Name
    Table   |schema2.tbl

ChangeLog:
    Date   |     Author      | Ticket | Modification
	2020-10-23 | Developer Name | T-123 | Test documentation of procedure
    2020-11-23 | Developer Name | T-124 | Updates to fix bugs in T-456
*/
    INSERT INTO schema2.tbl VALUES (p_bigint);
$BODY$
LANGUAGE SQL;