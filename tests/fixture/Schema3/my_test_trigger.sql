/*
Purpose:
This a new trigger to show how auto documentation can add new objects quickly.
Dependent Objects:
    Type    |Name
    Table   |my_test_schema.my_test_table
ChangeLog:
    Date    |    Author    |    Ticket    |    Modification
    2020-11-24    |    Developer_2    |    T-239    |    Initial Definition
*/

CREATE TRIGGER log_update
    AFTER UPDATE ON my_schema.my_test_table
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
    EXECUTE PROCEDURE log_my_test_table_update()
;
