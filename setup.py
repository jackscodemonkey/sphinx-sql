from setuptools import setup, find_packages
from spinx-sql import __version__

with open('README.md') as file:
    long_description = file.read()

setup(
    name='sphinx-sql',
    version=__version__,
    packages=find_packages(),
    url='',
    license='MIT',
    author='Marcus Robb',
    description="""Sphinx extension for autodoc of SQL files. """",
    long_description=long_description,
    install_requires=[
        'Sphinx'
    ],
    include_package_data=True,
)