AutoPlay: yaml orchestration for bash
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes I find make too old, autoplay unfrustrates me.

Getting started
---------------

Install with ``pip install autoplay``.

Create a file with name ``autoplay.yml`` containing::

    ---
    name: example
    example_var: ./autoplay-example
    multiline_var: |
      foo
      bar
    setup:
    - test -f $example_var || echo "$multiline_var" > $example_var
    script:
    - cat $example_var

Then, see the commands it would execute with ``autoplay example``...
