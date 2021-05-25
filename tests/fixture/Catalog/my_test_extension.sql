/*
Purpose:
This a new extension to show how auto documentation can add new objects quickly.
Dependent Objects:
    Type    |Name
    Schema   | my_test_schema
ChangeLog:
	Date    |    Author    |    Ticket    |    Modification
	2020-12-23    |  Developer_2  |   T-232    |    Initial Definition
*/

CREATE EXTENSION IF NOT EXISTS my_test_extension
	  WITH SCHEMA my_test_schema
	  VERSION '1.0.0'
;
