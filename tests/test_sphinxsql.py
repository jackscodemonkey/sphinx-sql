import pytest

pytestmark = pytest.mark.sphinx('html', testroot='directives')

def test_index(page):
    