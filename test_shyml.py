from cli2.test import autotest
import pytest


@pytest.mark.parametrize('path,cmd', [
    ('tests/hello_help.txt', './sh.yml help hello'),
    ('tests/hello_debug.txt', './sh.yml debug hello'),
    ('tests/install_help.txt', './sh.yml help install'),
    ('tests/test_debug.txt', './sh.yml debug test'),
    ('tests/test_args.txt', './sh.yml hello test'),
])
def test_shyml(path, cmd):
    autotest(path, cmd)
