import cli2


def test_hello_help():
    cli2.autotest('tests/hello_help.txt', 'shyml -h sh.yml hello')


def test_hello_debug():
    cli2.autotest('tests/hello_debug.txt', 'shyml -d sh.yml hello')


def test_install_debug():
    cli2.autotest('tests/install_help.txt', 'shyml -h sh.yml install')
