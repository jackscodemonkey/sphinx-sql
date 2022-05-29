# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import re
import sys
import datetime


sys.path.insert(0, os.path.abspath('../../'))
now = datetime.datetime.now()

VERSIONFILE="../../sphinx_sql/__init__.py"

with open(VERSIONFILE, "rt") as f:
        line = f.read()
        VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
        RELRE = VSRE = r"^__release__ = ['\"]([^'\"]*)['\"]"
        ver = re.search(VSRE, line, re.M)
        rel = re.search(RELRE, line, re.M)
        if ver:
            __version__ = ver.group(1)
        if rel:
            __release__ = rel.group(1)

# -- Project information -----------------------------------------------------

project = 'Sphinx-SQL'
copyright = f'{now.year}, Marcus Robb'
author = 'Marcus Robb'

# The full version, including alpha/beta/rc tags
version = __version__
release = __release__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx_sql.sphinx_sql',
    'sphinx_rtd_theme',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

#html_css_files = ['custom.css']

# -- Options for sphinx-sql --------------------------------------------------

# Disable extraction of Table Columns (Attributes Block) from DDL.
sphinxsql_include_table_attributes = True
