import cli2


def test_shyml_twine():
    cli2.autotest('tests/twine.txt', 'shyml twine')


def test_shyml():
    cli2.autotest('tests/shyml.txt', 'shyml')


def test_shyml_help():
    cli2.autotest('tests/help.txt', 'shyml help')


def test_shyml_help_twine():
    cli2.autotest('tests/help_twine.txt', 'shyml help twine', [
        'job from.*'
    ])
