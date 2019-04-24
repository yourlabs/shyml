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


@cli2.option(
    'debug', alias='d', color=cli2.GREEN, immediate=True,
    help='Dry run: output shell script for job',
)
@cli2.option(
    'shell', alias='s', color=cli2.GREEN, immediate=True,
    help='Shell to pipe commands to, default: /bin/bash -eux'
)
@cli2.option(
    'help', alias='h', color=cli2.GREEN, immediate=True,
    help='Output help for a job in sh.yml'
)
def run(path=None, job=None):
    """
    Render jobs defined in ./sh.yml or any sh.yml file.
    """
    if not path:
        yield from help()
        return

    if not os.path.exists(path):
        raise cli2.Cli2Exception(f'{path} does not exist')

    options = console_script.parser.options
    shell = options.get('shell', '/bin/bash -eux')

    schema = Schema.factory(path)

    if not job:
        yield from ls(schema)
        return

    job = schema[job]

    if options.get('help', False):
        yield job.help or f'No help for {job.name}'
        yield f'Try {cli2.GREEN}./sh.yml -h {job.name}{cli2.RESET}'
        return

    if console_script.parser.options.get('debug', False):
        # generate from schema to support hooks
        yield from schema.script(job.name)
        return

    fd, path = tempfile.mkstemp(prefix='.shyml', dir='.')
    with open(path, 'w') as f:
        for line in schema.script(job.name):
            f.write(line + '\n')

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
        yield 'For help of a job, run: -h JOB'
        yield 'For script of a job, run: -d JOB'
    else:
        yield f'{cli2.RED}Could not parse{cli2.RESET}: {schema.path} !'


def help(path=None, job=None):
    """
    Show help for a job.

    To get the list of jobs that you can get help for, run shyml without
    argument.
    """
    schema = Schema.factory(path)

    if not schema:
        yield 'sh.yml not found, please start with README'
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
        f'{cli2.GREEN}shyml -d {job}{cli2.YELLOW}',
        '',
        f'Run the generated bash for this job:',
        f'{cli2.GREEN}shyml {job}{cli2.RESET}',
    ]
    yield '\n'.join(out)


class ConsoleScript(cli2.ConsoleScript):
    def __init__(self, doc=None, argv=None, default_command='help'):
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            argv = [sys.argv[0]] + sys.argv[2:]
            os.environ['SHYML'] = sys.argv[1]
        super().__init__(doc, argv, default_command)


class Job(dict):
    @classmethod
    def factory(cls, doc, schema):
        job = cls(doc)
        job.doc = doc
        job.schema = schema
        job.name = doc['name']
        job.hook = doc.get('hook', None)
        job.env = doc.get('env', {})
        job.requires = doc.get('requires', [])
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
            yield from self.schema[name].script()

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
        for hook in self.hooks['before']:
            if hook.name == jobs[0]:
                continue
            yield from hook.script()

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
            yield from self[name].script()

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
).add_commands(run)
