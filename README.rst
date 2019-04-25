ShYml: write shell in sh.yml
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes gnu make reminds me how old I am, shyml makes me feel like a baby again.

Install
-------

Install with ``pip install shyml``.

.. note:: Use ``pip install --user`` for non-root install in ~/.local/bin.

Getting started
---------------

Create a executable yaml file in your repo with the following shebang::

   #!/usr/bin/env shyml

Then, start adding a YAML document in it.

Each YAML document (separated by `---`) should contain a `name` key.

Other keys it can define:

- script: a bash script in list or string format, arguments will be proxied
- help: a help text to describe the job
- color: a color to render the job name
- requires: the list of other jobs to execute prior to this job
- hook: set to `before` toautomatically execute before any other
- env: a YAML hash of env var

Example::

   #!/usr/bin/env shyml
   name: foo
   help: bar
   requires:
   - other
   script:
   - ./super
        long
        line

Usage:

.. code-block:: bash

   ./sh.yml                       # lists jobs
   ./sh.yml -d jobname            # print a job script code
   ./sh.yml -h jobname            # print a job help
   ./sh.yml jobname               # run a job in a local bash shell
