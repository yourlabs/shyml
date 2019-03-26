import cli2


def test_shyml_twine():
    cli2.autotest('tests/example.txt', './example.sh')


def test_shyml_help_twine():
    cli2.autotest('tests/help_twine.txt', 'shyml help twine', [
        'job from.*'
    ])
