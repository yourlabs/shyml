ShYml: write shell in sh.yml
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes gnu make reminds me how old I am, shyml makes me feel like a baby again.

Getting started
---------------

Install with ``pip install shyml``.

.. note:: Use ``pip install --user`` for non-root install in ~/.local/bin.

The ``shyml`` command will look for a file called ``sh.yml`` in the current
directory and list the jobs it finds. It will merge them with the default jobs
that are in the repository root and open for contributions ;)

Write your ``sh.yml`` file as such for example:

.. code-block:: yaml


    ---
    name: example
    color: red          # yes, you can choose the color of your job
    requires: other_job # disregard for now, it's for when your sh.yml grows up
    script:
    - myvar=x
    - some
         --super
         --long=$myvar
         line

    ---
    name: setup
    hook: before jobs   # this will always execute before any job
    script: |
      something cool
    env:
      someglobal: foo

You see, we have hooks, choosing colors to jobs (I choose so far: green for
non-writing, orange for writing, red for destructive), or doing super long
lines of shell commands without backslashes at the end are typically the kind
of things that make me feel like a baby again.

Without argument, ``shyml`` will just print out all jobs it finds.

With an argument that matches a defined job, it will just output the generated
shell script, you can pipe it to a shell if you want to execute it:

.. code-block:: bash

   shyml                       # lists jobs
   shyml jobname               # print a job in bash
   shyml jobname | bash -eux   # run a job in a local bash shell

Then you could see your generated bash with ``shyml example`` and execute it
with ``shyml example | docker run -it yourcontainer sh`` or something.
