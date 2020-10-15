from . import __version__
from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import Directive, directives

import sphinx
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.util import logging

logger = logging.getLogger(__name__)

class SqlDirective(Directive):

    has_content = False
    option_spec = {'sqlsource': directives.unchanged}

    def get_sql_dir(self, sqlsrc):
        env = Path(self.state.document.settings.env.srcdir)
        path = Path.resolve(Path.joinpath(env, sqlsrc))
        return path

    def get_sql_files(self, srcpath):
        files = Path(srcpath).rglob('*.sql')
        for file in files:
            logger.info("File: {}".format(file))
        return files

    def run(self):
        sql_argument = self.options['sqlsource']
        srcdir = self.get_sql_dir(sqlsrc=sql_argument)
        sql_files = self.get_sql_files(srcpath=srcdir)
        sections = []
        return sections

def setup(app):
    app.add_directive("autopgsql", SqlDirective)
    return {
        'version': __version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }