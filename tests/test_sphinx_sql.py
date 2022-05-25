import pytest
from types import SimpleNamespace
from sphinx_sql.sphinx_sql import SqlDirective
from unittest.mock import patch, mock_open


@pytest.fixture
def table_definition():
    definition = """
    /*
    Purpose:
    This a new table to show how auto documentation can add new objects quickly.
    ChangeLog:
        Date    |    Author    |    Ticket    |    Modification
        2020-10-26    |  Developer_2  |   T-220    |    Initial Definition
    */
    CREATE TABLE myschema.mytable(
        id BIGSERIAL,
        f_name text,
        l_name varchar(100)
    )
    DISTRIBUTED BY (id);
    """
    return definition


@pytest.fixture
def function_definition():
    definition = """
    /*
    Parameters:
    Name | Type | Description
    debug | boolean | Toggle debug on or off, default False

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
            YYYY-MM-DD |        Developer name |        T-223 | Short Modification details or some really long text that will continue on.
    */
    CREATE OR REPLACE FUNCTION schema1.fn_function(debug BOOLEAN) RETURNS void
    AS $BODY$
    DECLARE
        v_source_rec_cnt BIGINT;
        v_fstart_ts TIMESTAMP;
        v_fend_ts TIMESTAMP;
    BEGIN
        SELECT 1;
    END;
    $BODY$
    LANGUAGE pgpgsql;
    """
    return definition


@pytest.fixture
def function_definition_no_dependents():
    definition = """
    /*
    Parameters:
    Name | Type | Description
    debug | boolean | Toggle debug on or off, default False

    Return: Void
    Purpose:
    Detailed explanation of the function which includes:
            - Function business logic
            - Transformation rules
            - Here is a bit more text.
    Dependent Objects:
        Type    |Name

    ChangeLog:
        Date   |     Author      |    Ticket | Modification
            YYYY-MM-DD |        Developer name |        T-223 | Short Modification details or some really long text that will continue on.
    */
    CREATE OR REPLACE FUNCTION schema1.fn_function(debug BOOLEAN) RETURNS void
    AS $BODY$
    DECLARE
        v_source_rec_cnt BIGINT;
        v_fstart_ts TIMESTAMP;
        v_fend_ts TIMESTAMP;
    BEGIN
        SELECT 1;
    END;
    $BODY$
    LANGUAGE pgpgsql;
    """
    return definition


@pytest.fixture
def view_definition():
    definition = """
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
    CREATE OR REPLACE VIEW myschema.myview AS
    SELECT * FROM myschema.mytable;
    """
    return definition


@pytest.fixture
def dml_definition():
    definition = """
    /*
    Object Name: my_test_dml
    Object Type: DML
    Purpose:
    A test DML definition.
    Dependent Objects:
        Type    |Name
        Table   |my_test_schema.my_test_table
    ChangeLog:
        Date    |    Author    |    Ticket    |    Modification
        2020-10-26    |  Developer_2  |   T-220    |    Initial Definition
    */

    DELETE FROM my_test_schema.my_test_table;
    """
    return definition


@pytest.fixture
def configuration():
    conf = {"sphinxsql_include_table_attributes": True}
    return SimpleNamespace(**conf)


def test_view_definitions(view_definition):
    view_text = view_definition
    with patch("builtins.open", mock_open(read_data=view_text)) as mock_file:
        s = SqlDirective(None, None, None, None, None, None, None, None, None)
        core = s.extract_core_text(config=configuration, file=mock_file)
        section = s.build_docutil_node(core)
        assert section.children[0].rawsource == "myschema.myview"


def test_function_definitions(function_definition):
    function_text = function_definition
    with patch("builtins.open", mock_open(read_data=function_text)) as mock_file:
        s = SqlDirective(None, None, None, None, None, None, None, None, None)
        core = s.extract_core_text(config=configuration, file=mock_file)
        section = s.build_docutil_node(core)
        contains_depenents = [
            x for x in section.children if x.rawsource == "DEPENDANT OBJECTS:"
        ]
        assert section.children[0].rawsource == "schema1.fn_function"
        assert len(contains_depenents) > 0


def test_function_definitions_no_dependents(
    function_definition_no_dependents, configuration
):
    function_text = function_definition_no_dependents
    with patch("builtins.open", mock_open(read_data=function_text)) as mock_file:
        s = SqlDirective(None, None, None, None, None, None, None, None, None)
        core = s.extract_core_text(config=configuration, file=mock_file)
        section = s.build_docutil_node(core)
        contains_dependents = [
            x for x in section.children if x.rawsource == "DEPENDANT OBJECTS:"
        ]
        assert section.children[0].rawsource == "schema1.fn_function"
        assert len(contains_dependents) == 0


def test_dml_definitions(dml_definition):
    dml_text = dml_definition
    with patch("builtins.open", mock_open(read_data=dml_text)) as mock_file:
        s = SqlDirective(None, None, None, None, None, None, None, None, None)
        core = s.extract_core_text(config=configuration, file=mock_file)
        section = s.build_docutil_node(core)
        assert section.children[1].rawsource == "OBJECT TYPE: DML"


def test_table_node_colums_on(table_definition, configuration):
    table_text = table_definition
    with patch("builtins.open", mock_open(read_data=table_text)) as mock_file:
        s = SqlDirective(None, None, None, None, None, None, None, None, None)
        core = s.extract_core_text(config=configuration, file=mock_file)
        section = s.build_docutil_node(core)
        assert section.children[0].rawsource == "myschema.mytable"
        assert section.children[6].rawsource == "ATTRIBUTES:"


def test_table_node_colums_off(table_definition, configuration):
    table_text = table_definition
    configuration.sphinxsql_include_table_attributes = False
    with patch("builtins.open", mock_open(read_data=table_text)) as mock_file:
        s = SqlDirective(None, None, None, None, None, None, None, None, None)
        core = s.extract_core_text(config=configuration, file=mock_file)
        section = s.build_docutil_node(core)
        assert section.children[0].rawsource == "myschema.mytable"
        assert section.children[6].rawsource == "CHANGE LOG:"
