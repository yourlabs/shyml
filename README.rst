AutoPlay: yaml orchestration for bash
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes I find make too old, autoplay unfrustrates me.

Getting started
---------------

Install with ``pip install autoplay``.

It will look for jobs in ``autoplay.yml`` in the current directory or fallback
on the ``autoplay/autoplay.yml`` file which defines a few default jobs. The
twine job for example will build .po files and make a python package that it
will upload with twine, to automate python package release::

    autoplay debug twine
    autoplay twine mode=dryrun
    TWINE_USERNAME=... TWINE_PASSWORD=.. autoplay twine

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

In-development
==============

CLI Development Environment
---------------------------

We're investing in a development command that would allow to run several jobs
simultaneously, with an `urwid
<https://urwid.org>`_ based interface. It would allow to define jobs like this
in your autoplay.yml::

    ---
    name: dev
    script:
    - eslint --watch
    - yarn start
    - django-admin runserver
    - py.test --watch

That you could run with ``autoplay run dev mode=ide``.

Tox-like and docker based executors
-----------------------------------

The default executor is ``linux`` which executes in a bash subshell.
However other executors are available such as ``executor=docker`` (for
baking development environments) and ``executor=virtualenv`` (for build
matrix).
