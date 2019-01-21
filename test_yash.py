import cli2


def test_yash_twine():
    cli2.autotest('tests/twine.txt', 'yash twine')


def test_yash():
    cli2.autotest('tests/yash.txt', 'yash')


def test_yash_help():
    cli2.autotest('tests/help.txt', 'yash help')


def test_yash_help_twine():
    cli2.autotest('tests/help_twine.txt', 'yash help twine', [
        'job from.*'
    ])
