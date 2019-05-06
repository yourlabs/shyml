import cli2
import pytest


@pytest.mark.parametrize('path,cmd', [
    ('tests/hello_help.txt', 'shyml sh.yml help hello'),
    ('tests/hello_debug.txt', 'shyml sh.yml debug hello'),
    ('tests/install_help.txt', 'shyml sh.yml help install'),
    ('tests/typo.txt', 'shyml sh.yml foo'),
    ('tests/typo_help.txt', 'shyml help sh.yml foo'),
    ('tests/typo_debug.txt', 'shyml debug sh.yml foo'),
])
def test_shyml(path, cmd):
    cli2.autotest(path, cmd)
