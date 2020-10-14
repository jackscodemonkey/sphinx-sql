from docutils import nodes
from docutils.parsers.rst import Directive

import sphinx
from sphinx.application import Sphinx
from sphinx.util import logging

logger = logging.getLogger(__name__)

class PgSql(Directive):

    def run(self):
        pass

def setup(app Sphinx) -> Dict[str, Any]:
    app.add_directive("autopgsql", PgSql)
    return {
        'version': __version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }