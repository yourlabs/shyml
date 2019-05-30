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

Examples
========

Replace tox.ini
---------------

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

Embed docker-compose.yml
------------------------

::

   ---
   name: compose
   script: |
     docker-compose -p $(pwd) -f <(cat <<EOF
     version: '3.5'
     services:
       django:
         build:
           dockerfile: Dockerfile
           context: ./
           shm_size: 512mb
         depends_on:
         - postgres
         volumes:
         - ./:/app

       postgres:
         image: postgres:10
     EOF
     ) $@

Replace Dockerfile with buildah
-------------------------------

::

   ---
   name: buildah
   script:
   - buildcntr1=$(buildah from --quiet docker.io/node:10-alpine)
   - buildmnt1=$(buildah mount $buildcntr1)
   - buildah config
       --env DJANGO_SETTINGS_MODULE=mrs.settings
       --env UWSGI_MODULE=mrs.wsgi:application
       --env NODE_ENV=production
       --env PYTHONIOENCODING=UTF-8
       --env PYTHONUNBUFFERED=1
       --env STATIC_URL=/static/
       --env STATIC_ROOT=/app/static
       --env UWSGI_SPOOLER_NAMES=mail,stat
       --env UWSGI_SPOOLER_MOUNT=/app/spooler
       --env VIRTUAL_PROTO=uwsgi
       --env LOG=/app/log
       --env VIRTUAL_PROTO=uwsgi
       --env GIT_COMMIT=$CI_COMMIT_SHA
       $buildcntr1
   - mkdir -p .cache/{apk,pip,npm}
   - buildah run -v $(pwd)/.cache/apk:/root/.cache/apk $buildcntr1
       apk add
       --update
       --cache-dir /root/.cache/apk
       ca-certificates
       gettext
       shadow
       python3
       py3-pillow
       py3-psycopg2
       dumb-init
       bash
       git
       curl
       uwsgi-python3
       uwsgi-http
       uwsgi-spooler
       uwsgi-cache
       uwsgi-router_cache
       uwsgi-router_static
   - buildah -v $(pwd)/.cache/pip:/root/.cache/pip run $buildcntr1
       pip3 install --upgrade pip
   - buildah run $buildcntr1
       bash -c 'curl -sL https://sentry.io/get-cli/ | bash'
   - buildah run $buildcntr1
       bash -c 'mkdir -p /app && usermod -d /app -l app node && groupmod -n app node && chown -R app:app /app'

   - buildah config --workingdir /app $buildcntr1

   - buildah copy $buildcntr1
       yarn.lock .babelrc package.json webpack.config.js /app/
   - buildah run $buildcntr1
       yarn install --frozen-lockfile
   - buildah copy $buildcntr1
       src/mrs/static /app/src/mrs/static
   - buildah run $(pwd)/.cache/npm:/npm $buildcntr1
       yarn --cache-folder /npm prepare

   - buildah copy $buildcntr1
       requirements.txt /app/
   - buildah run -v $(pwd)/.cache/pip:/root/.cache/pip $buildcntr1
       pip3 install --upgrade -r /app/requirements.txt

   - buildah run $buildcntr1 bash
   - buildah copy $buildcntr1
       setup.py src /app/
   - buildah run $buildcntr1 bash
   - buildah run -v $(pwd)/.cache/pip:/root/.cache/pip $buildcntr1
       pip3 install --editable /app

   - buildah run $buildcntr1
       mkdir -p /app/{log,static}
   - buildah run $buildcntr1
       mrs collectstatic --noinput --clear
   - buildah copy $buildcntr1
       locale /app/locale
   - buildah run $buildcntr1
       mrs compilemessages -l fr
   - buildah run $buildcntr1
       'find $STATIC_ROOT -type f | xargs gzip -f -k -9'

