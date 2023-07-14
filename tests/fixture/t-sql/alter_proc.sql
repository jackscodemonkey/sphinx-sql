/*
Parameters:
Name | Type | Description

Return: Void
Purpose:
    - Detailed explanation of the procedure which includes:
    - Procedure: business logic
    - Transformation rules
    - t-sql example of alter procedure
Dependent Objects:
    Type    |Name

ChangeLog:
    Date   |     Author      | Ticket | Modification
	2023-07-13 | Developer Name | T-123 | Test documentation of procedure
*/
alter procedure myschema.alter_myproc
@i int = 0
as
begin
select 'Hello', @i
end