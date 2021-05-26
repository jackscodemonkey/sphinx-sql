/*
Purpose:
This a extension with a quoted name to show how auto documentation can add new objects quickly.
Dependent Objects:
	Type    |Name
	Schema   | my_test_schema
ChangeLog:
	Date    |    Author    |    Ticket    |    Modification
	2020-12-26    |  Developer_2  |   T-245    |    Initial Definition
*/

CREATE EXTENSION "uuid-ossp"
    WITH SCHEMA my_test_schema
;
