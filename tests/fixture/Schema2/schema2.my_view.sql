/*
Purpose:
Testing a view definition
Dependent Objects:
    Type    |Name
    Table   |util.table_owners
ChangeLog:
    Date    |    Author    |    Ticket    |    Modification
    2020-01-01    |    Developer Name    |    T-154    |    Initial Definition
*/

CREATE OR REPLACE VIEW schema2.my_view AS
BEGIN
    SELECT meh from public.tbl1;
END;