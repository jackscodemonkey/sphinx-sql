import pytest
from sphinx.application import Sphinx


@pytest.fixture
def sphinx_project(self, tmpdir):
    src_dir = tmpdir.mkdir('src')
    out_dir = tmpdir.mkdir('out')
    # add_file(src_dir, 'conf.py', '''
    # extensions = [ 'sphinx_sql.sphinx_sql' ]
    # ''')
    yield src_dir, out_dir
 
