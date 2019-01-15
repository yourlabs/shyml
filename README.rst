YaSH: YAML to Bash
~~~~~~~~~~~~~~~~~~

Sometimes I make reminds me how old I am, yash makes me feel like a baby again.

Getting started
---------------

Install with ``pip install yash``.

The yash command will print out the jobs it find. Pipe it to bash if you want
to execute what it generates:

.. code-block:: bash

   yash                       # lists jobs
   yash jobname               # print a job in bash
   yash jobname | bash -eux   # run a job in a local bash shell

It will look for jobs in a ``yash.yml`` file that you could write as such:

.. code-block:: yaml

    ---
    env:
      someglobal: foo

    ---
    name: example
    script:
    - myvar=x
    - some
         --super
         --long=$myvar
         line

Then you could see your generated bash with `yaml example` and execute it with
`yaml example | bash -eux` or something.
