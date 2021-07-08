import pytest
from sphinx.application import Sphinx
from sphinx_sql.sphinx_sql import SqlDirective
from docutils.parsers.rst import Directive, directives

@pytest.fixture
def sphinx_project(self, tmpdir):
    src_dir = tmpdir.mkdir('src')
    out_dir = tmpdir.mkdir('out')
    # add_file(src_dir, 'conf.py', '''
    # extensions = [ 'sphinx_sql.sphinx_sql' ]
    # ''')
    yield src_dir, out_dir


def test_extract_comments():
    s = SqlDirective(None, None, None, None, None, None, None, None, None)
    sql_content = """
        /*
        Object Name: my_test_dml
        Object Type: DML
        Purpose:
        This a new view to show how auto documentation can add new objects quickly.
        
        ChangeLog:
            Date    |    Author    |    Ticket    |    Modification
            2020-10-26    |  Developer_2  |   T-220    |    Initial Definition
        */
        
        SELECT * FROM my_test_schema.my_test_table;    
    """
    extracted = s.extract_comments(str_comment=sql_content)
    assert extracted['purpose'] == 'This a new view to show how auto documentation can add new objects quickly.'
