ShYml: write shell in sh.yml
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes gnu make reminds me how old I am, shyml makes me feel like a baby again.

Getting started
---------------

Install with ``pip install shyml``.

.. note:: Use ``pip install --user`` for non-root install in ~/.local/bin.

And then you can add files like that to your repositories:

.. code-block:: yaml

  #!/usr/bin/env shyml
  name: test
  help: Testing commands
  script: some command
  hook: before  # inject this job prior to others
  env:
    GLOBAL_ENV: something

  ---
  name: test.reset
  help: Example subcommand
  env:
    LOCAL_ENV: other
  script:
  - echo $GLOBAL_ENV $LOCAL_ENV
  - some
       --super
       --long=$myvar
       line
  - ./sh.yml test

Usage:

.. code-block:: bash

   ./sh.yml                       # lists jobs
   ./sh.yml -d jobname            # print a job script code
   ./sh.yml jobname               # run a job in a local bash shell
