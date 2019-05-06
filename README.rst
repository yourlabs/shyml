ShYml: write shell in sh.yml
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes gnu make reminds me how old I am, shyml makes me feel like a baby again.

Getting started
===============

Install
-------

Install with ``pip install shyml``.

.. note:: Use ``pip install --user`` for non-root install in ~/.local/bin.

Executable and shebang
----------------------

Create a executable yaml file in your repo (name it ``sh.yml`` by convention)
with shyml in the shebang as such::

   #!/usr/bin/env shyml

Then, start adding a YAML document in it.

Example
-------

.. code-block:: yaml

   #!/usr/bin/env shyml
   name: foo
   help: bar
   requires:
   - other
   script:
   - ./super
        long
        line
   - shyml_otherjob     # call another job as a bash function
   ---
   name: otherjob
   script: |
     your code here

Document model
--------------

Each YAML document (separated by `---`) should contain a `name` key.

Other keys it can define:

- script: a bash script in list or string format, arguments will be proxied
- help: a help text to describe the job
- color: a color to render the job name
- requires: the list of other jobs to execute prior to this job
- hook: set to `before` toautomatically execute before any other
- env: a YAML hash of env var

CLI Usage
---------

.. code-block:: bash

   ./sh.yml                       # lists jobs
   ./sh.yml jobname               # run a job in a local bash shell
   shell=xonsh ./sh.yml jobname   # apparently you your sh.yml contains xonsh instead of bash ^^
   ./sh.yml debug jobname         # print a job script code
   ./sh.yml test jobname          # print a job help

Example replacing tox.ini
-------------------------

So, initially shyml was born because I wanted to get too much out of tox.
Namely, centralizing test automation and eventually deployment (for integration
testing) in a single multi-script file, for usage in various contexts:

- in the system python environment, ie. in a built container
- in the user python environment, that is where i have checked out all
  development source code I want to hack at the version that I develop with
  (and I try hard to stick to upstream and have forward-compatible code)
- in a virtualenv, to test against released module versions.

To address this, I use such shyml job, that will make a venv with python3 by
default, not setup any venv if venv=none, and use the user environment if
venv=user.

.. code-block:: yaml

   ---
   name: install
   help: |
     Setup and activate a venv for a python executable

     If venv=none, it will not do any venv.
     If venv=user, it will use pip install --user.
   script: |
     if [ "${venv-}" = "user" ]; then
       pip_install="pip install --user"
     elif [ "${venv-}" != "none" ]; then
       export python="${python-python3}"
       export path="${path-.venv.$python}"
       test -d $path || virtualenv --python=$python $path
       set +eux; echo activating $path; source $path/bin/activate; set -eux
     fi
     ${pip_install-pip install} -Ue .[test]

   ---
   name: test
   help: Run test in a python3 venv by default.
   script: shyml_install && py.test -vv --cov src --strict -r fEsxXw ${@-src}

Then, I can run:

.. code-block::

   venv=user ./sh.yml test       # in my home
   venv=none ./sh.yml test       # in a built container
   ./sh.yml test                 # just run tests in the default venv tox-like
