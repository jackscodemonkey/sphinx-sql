Introduction
^^^^^^^^^^^^

sphinx-sql is a Sphinx documentation extension for building documentation from SQL source files.

| * Do you live in a bottomless pit of despair with "Living documents" in Sharepoint.
| * Have you had to troubleshoot a problem and someone has reorganized the documentation tree in Sharepoint?
| * Has your company let PMs loose on projects with no idea how to version documentation, so now you have copies of entire doc trees in Sharepoint?
|
| * Do you work on a database first development project?
| * Do you look at auto documentation packages and cry silently because no one cares about DB first development?
| * Don't you wish you could maintain your project documentation with your code base, so you can check out and build the documents anytime you need them?

Having found nothing in the while that could help solve the db first problem, I've written sphinx-sql.

| The goal of sphinx-sql is to provide an autodoc type module for database first development.
| With a bit of standardization of comments in the top of the sql source files, we can maintain documentation that follows the code base.

This implementation is tested against Greenplum / Postgres, those are the databases I work with on a daily basis.
If you want to extend functionality, have a quick look at the contrib section of this document.

*Tip:* If you create your DDL with pgModeler,
you may want to look into this `simple script`_
to conveniently generate single DDL files, which can be handled by sphinx-sql.

.. _simple script: https://github.com/winkelband/ddlsplit

Installation
^^^^^^^^^^^^

Install from PyPI:

.. code-block:: bash

    pip install sphinx-sql

Configuration
^^^^^^^^^^^^^

Configuring Sphinx
==================

In your conf.py for Sphinx enable the extension:

.. code-block:: python

    extensions = [
    'sphinx_sql.sphinx_sql',
    ]

Add the option to toggle including table attributes:

.. code-block:: python

    sphinxsql_include_table_attributes = True

By default, Table Columns with their metadata (data type, length, precision, scale) are extracted from the DDL.
You can disable this behavior by changing sphinxsql_include_table_attributes = False in your conf.py.


Configure toctree
=================

Create a new rst file (we'll call it autosql.rst) and include it in your toc-tree.

.. code-block:: RST

   .. toctree::
   :maxdepth: 2
   :caption: Navigation:

   autosql

Configure rst
=============

Add the directive with a relative path from your document build folder to the root of your SQL source in the autosql.rst file.

.. code-block:: RST

    SQL Documentation
    ^^^^^^^^^^^^^^^^^

    .. autosql::
        :sqlsource: ../../SQL

Add SQL Comments
================

| sphinx-sql recursively looks for all .sql files under the configured sqlsource path.
| It will extract the first block comment out of each file as well as important
| object creation lines such as CREATE TABLE / VIEW  / FUNCTION / LANGUAGE etc.
|
| Comments should adhere to the following formats, otherwise the regex searches will not find the appropriate blocks
| Pipe delimiters are used in Parameters, Dependent Objects and Change Log files to create table rows in the documents, spaces don't matter; everything else is free form text and should appear as you write it.
|

**Key word groups:**

| Parameters:
| Return:
| Purpose:
| Dependent Objects:
| ChangeLog:
|

**FUNCTIONS:**

.. code-block:: SQL

   /*
    Parameters:
    Name | Type | Description

    Return: Void
    Purpose:
    Detailed explanation of the function which includes:
            - Function business logic
            - Transformation rules
            - Here is a bit more text.
    Dependent Objects:
        Type    |Name
        Table   |schema_name.source_table5
        View    |schema_name.target_table6
    ChangeLog:
        Date   |     Author      |    Ticket | Modification
	    YYYY-MM-DD |	Developer name |	T-223 | Short Modification details or some really long text that will continue on.
    */

**PROCEDURES:**

.. code-block:: SQL

   /*
    Parameters:
    Name | Type | Description

    Purpose:
    Detailed explanation of the procedure which includes:
            - Procedure business logic
            - Transformation rules
            - Here is a bit more text.
    Dependent Objects:
        Type    |Name
        Table   |schema_name.source_table5
        View    |schema_name.target_table6
    ChangeLog:
        Date   |     Author      |    Ticket | Modification
	    YYYY-MM-DD |	Developer name |	T-223 | Short Modification details or some really long text that will continue on.
    */

**TABLES/VIEWS/etc:**

You can comment on Table Columns (one-line text, no markups) in your DDL (``COMMENT ON COLUMN``).
These comments will appear in the "Description" column inside the Attributes Block.

.. code-block:: SQL

    /*
    Purpose:
    This a new view to show how auto documentation can add new objects quickly.
    Dependent Objects:
        Type    |Name
        Table   |schema1.ext_table
    ChangeLog:
        Date    |    Author    |    Ticket    |    Modification
        2020-10-26    |  Developer_2  |   T-220    |    Initial Definition
    */

**DML:**

| Files that are not a SQL object, but you'd like to include in documentation,
| can be included by providing key information in the top-level comment.
| Object Name, Object Type are required fields in order to categorize and sort the output.
| The remainder of the keywords are valid for use in DML blocks.

.. code-block:: SQL

    /*
    Object Name: <schema.name>
    Object Type: DML
    Purpose:
    This a new view to show how auto documentation can add new objects quickly.

    ChangeLog:
        Date    |    Author    |    Ticket    |    Modification
        2020-10-26    |  Developer_2  |   T-220    |    Initial Definition
    */
