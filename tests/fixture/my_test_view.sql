/*
Purpose:
This a new view to show how auto documentation can add new obejcts quickly.
Dependent Objects:
    Type    |Name
    Table   | schema1.ext_table
ChangeLog:
    Date    |    Author    |    Ticket    |    Modification
    2020-10-26    |    Developer_2    |    T-220    |    Initial Definition
*/

CREATE OR REPLACE VIEW schema3.my_new_test_view AS
BEGIN
    SELECT meh from public.tbl1;
END;