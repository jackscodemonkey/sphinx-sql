import pytest
from sphinx.application import Sphinx

@pytest.fixture
def sphinx_project(tempdir):
    srcdir = tmpdir.mkdir('src')
    outdir = tmpdir.mkdir('out')
    add_file(srcdir, 'conf.py', '''
    extensions = [ 'sphinx_sql.sphinx_sql' ]
    ''')
    yield (srcdir, outdir)
 
