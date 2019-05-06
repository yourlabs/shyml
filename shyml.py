"""
Orchestrate shell script units from a single sh.yml file.
"""

import cli2
import colorama
import os
import shlex
import subprocess
import sys
import tempfile
import yaml


LOGO = f'{cli2.GREEN}Sh{cli2.YELLOW}Y{cli2.RED}ml{cli2.RESET}'


class JobCommand:
    def __init__(self, name):
        self.__name__ = name

    def __call__(self, path=None, job=None, *args):
        """
        Render jobs defined in ./sh.yml or any sh.yml file.
        """
        if not path:
            yield from help()
            return

        if not os.path.exists(path):
            raise cli2.Cli2Exception(f'{path} does not exist')

        schema = Schema.factory(path)

        if not job:
            yield from ls(schema)
            return

        if job not in schema:
            yield f'{cli2.RED}{job}{cli2.RESET} not found in {schema.path}'
            return

        self.job = schema[job]
        yield from self.execute()


class JobRun(JobCommand):
    def execute(self):
        fd, path = tempfile.mkstemp(prefix='.shyml', dir='.')
        with open(path, 'w') as f:
            for line in self.job.schema.script(self.job.name):
                f.write(line + '\n')

        shell = os.getenv('shell', '/bin/bash -eux')
        shell_arg = shell.split(' ') + [path]

        # 1337 ArGv InJeC710n H4ck: proxying argv from: shyml sh.yml JOB foobar
        # And: proxying argv from: ./sh.yml JOB foobar
        # Will cause $1 to be "foobar" in the script content of JOB
        shell_arg += console_script.argv[3:]

        proc = subprocess.Popen(
            shell_arg,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        proc.communicate()
        os.unlink(path)
        sys.exit(proc.returncode)


class JobDebug(JobCommand):
    def execute(self):
        yield from self.job.schema.script(self.job.name)


run = JobRun('run')
debug = JobDebug('debug')


def ls(schema, prefix=None):
    if schema:
        yield f'{LOGO} has found the following jobs:'
        yield ''

        width = len(max(schema.keys(), key=len)) + 1

        for name in sorted(schema.keys()):
            display = name
            job = schema[name]
            line = ' '

            line += job.color_code
            line += name
            line += cli2.RESET

            line += (width - len(display)) * ' '
            line += job.help.split('\n')[0]

            yield line
        yield ''
        yield 'Print out script of a job: ./sh.yml debug JOB'
        yield 'Print out help of a job: ./sh.yml help JOB'
    else:
        yield f'{cli2.RED}Could not parse{cli2.RESET}: {schema.path} !'


def help(path, job=None):
    """
    Show help for a job.

    To get the list of jobs that you can get help for, run shyml without
    argument.
    """
    schema = Schema.factory(path)

    if not schema:
        yield 'sh.yml not found, please start with README'
        return

    if not job:
        yield 'Job not specified, showing job list'
        yield from ls(schema)
        return

    if job not in schema:
        yield f'{cli2.RED}{job}{cli2.RESET} not found in {schema.path}'
        return

    out = [
        ' '.join([
            'Showing help for',
            ''.join([
                cli2.GREEN,
                job,
                cli2.RESET,
            ]),
        ]),
        schema[job].help,
        f'Output generated bash job:',
        f'{cli2.GREEN}shyml debug {job}{cli2.YELLOW}',
        '',
        f'Run the generated script for this job:',
        f'{cli2.GREEN}shyml {job}{cli2.RESET}',
    ]
    yield '\n'.join(out)


class Job(dict):
    @classmethod
    def factory(cls, doc, schema):
        job = cls(doc)
        job.doc = doc
        job.schema = schema
        job.name = doc['name']
        job.hook = doc.get('hook', None)
        job.env = doc.get('env', {})
        job.requires = doc.get('requires', doc.get('require', []))
        if isinstance(job.requires, str):
            job.requires = [job.requires]
        job.help = doc.get('help', '')
        job.color = doc.get('color', 'yellow')
        job.color_code = getattr(colorama.Fore, job.color.upper(), cli2.RESET)
        return job

    def visit(self, schema):
        self.parent = None
        self.children = []

        for job in schema.values():
            if job is self:
                continue

            if job.name.startswith(self.name):
                self.children.append(job)

            if self.name.startswith(job.name):
                if not self.parent:
                    self.parent = job
                elif len(self.parent.name) < job.name:
                    self.parent = job

    def script(self):
        env = dict()
        for name in self.requires:
            if self.schema[name].env:
                env.update(self.schema[name].env)
        env.update(self.env)

        for key, value in env.items():
            yield ''.join(['export ', str(key), '=', shlex.quote(str(value))])

        for name in self.requires:
            yield 'shyml_' + name

        script = self.get('script')
        if not script:
            return

        if not isinstance(script, list):
            script = [l for l in script.split('\n') if l.strip()]

        for chunk in script:
            if chunk:
                yield chunk


class Schema(dict):
    def __init__(self, path):
        self.hooks = {
            'before': [],
        }
        self.path = path

    def script(self, *jobs):
        for job in self.values():
            yield 'shyml_' + job.name + '() {'
            if job.help:
                for line in job.help.strip().split('\n'):
                    yield f'    # {line}'
            for line in self[job.name].script():
                yield f'    {line}'
            yield '}'

        for hook in self.hooks['before']:
            if hook.name == jobs[0]:
                continue
            yield 'shyml_' + hook.name

        for name in jobs:
            if name not in self:
                raise cli2.Cli2Exception(''.join([
                    cli2.RED,
                    'Job not found: ',
                    cli2.RESET,
                    name,
                    '\n',
                    cli2.GREEN,
                    'Job founds:',
                    cli2.RESET,
                    '\n',
                    '\n'.join([f'- {i}' for i in sorted(self.keys())]),
                ]))
            yield 'shyml_' + name

    def parse(self):
        with open(self.path, 'r') as f:
            docs = [
                yaml.load(i, Loader=yaml.SafeLoader)
                for i in f.read().split('---') if i.strip()
            ]

        for doc in docs:
            if not doc:
                continue

            name = doc.get('name')
            job = self[name] = Job.factory(doc, self)

            if job.hook:
                self.hooks[job.hook].append(job)

        for job in self.values():
            job.visit(self)

    @classmethod
    def factory(cls, path=None):
        path = path or os.getenv('SHYML', 'sh.yml')

        self = cls(path)
        if not os.path.exists(path):
            print(f'{cli2.RED}Could not find{cli2.RESET} {path}')
        else:
            self.parse()

        return self


console_script = cli2.ConsoleScript(
    __doc__,
    default_command='run'
).add_commands(run, help, debug)
