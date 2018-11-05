AutoPlay: yaml orchestration for bash
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes I find make too old, autoplay unfrustrates me.

Getting started
---------------

Install with ``pip install autoplay``.

Try a builting example with command::

    autoplay run twine pypi_user=jpic pypi_pass=lol mode=dryrun

Create a file with name ``autoplay.yml`` containing::

    ---
    env:
      someglobal: foo

    ---
    name: example
    env:
      example_var: ./autoplay-example
      multiline_var: |
        foo
        bar
    setup:
    - test -f $example_var || echo "$multiline_var" > $example_var
    script:
    - cat $example_var

    ---
    name: test
    requires:
    - example

Then, see the commands it would execute with ``autoplay run example mode=dryrun``...
