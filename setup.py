from setuptools import setup, find_packages
from sphinx_sql import __version__, __release__
from sphinx.setup_command import BuildDoc
cmdclass = {'build_sphinx': BuildDoc}

with open('README.md') as file:
    long_description = file.read()

version = __version__
release = __release__
name = 'sphinx-sql'

setup(
    name=name,
    version=release,
    packages=find_packages(),
    url='',
    license='MIT',
    author='Marcus Robb',
    description="Sphinx extension for autodoc of SQL files.",
    long_description=long_description,
    install_requires=[
        'Sphinx'
    ],
    include_package_data=True,
    cmdclass=cmdclass,
    command_options={
        'build_sphinx': {
            'project': ('setup.py', name),
            'version': ('setup.py', version),
            'release': ('setup.py', release),
            'source_dir': ('setup.py', 'docs/source'),
            'build_dir': ('setup.py', 'docs/build')
        }
    }
)