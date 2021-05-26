/*
Purpose:
This a new materialized view to show how auto documentation can add new objects quickly.
Dependent Objects:
    Type    |Name
    Table   |my_test_schema.my_test_table
ChangeLog:
    Date    |    Author    |    Ticket    |    Modification
    2020-11-24    |    Developer_2    |    T-237    |    Initial Definition
*/

CREATE MATERIALIZED VIEW my_test_schema.my_test_materialized_view AS
    SELECT name FROM my_test_schema.my_test_table
WITH NO DATA
;
