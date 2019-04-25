import cli2


def test_hello_help():
    cli2.autotest('tests/hello_help.txt', 'shyml -h sh.yml hello')


def test_hello_debug():
    cli2.autotest('tests/hello_debug.txt', 'shyml -d sh.yml hello')


def test_install_debug():
    cli2.autotest('tests/install_help.txt', 'shyml -h sh.yml install')


def test_typo():
    cli2.autotest('tests/typo.txt', 'shyml sh.yml foo')


def test_typo_help():
    cli2.autotest('tests/typo_help.txt', 'shyml -h sh.yml foo')


def test_typo_debug():
    cli2.autotest('tests/typo_debug.txt', 'shyml -d sh.yml foo')
