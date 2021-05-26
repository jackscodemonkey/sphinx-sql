/*
Purpose:
This a new user to show how auto documentation can add new objects quickly.
It inherits permissions from my_test_role.
Dependent Objects:
    Type    |Name
    Role    |my_test_role
ChangeLog:
	Date    |    Author    |    Ticket    |    Modification
	2020-12-23    |  Developer_2  |   T-234    |    Initial Definition
*/
CREATE USER person_doe WITH
    PASSWORD '1234pass'
    LOGIN
    ROLE an_other
;
