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
    'debug', alias='d', color=cli2.GREEN,
    help='Dry run: output shell script for job'
)
@cli2.option(
    'shell', alias='s', color=cli2.GREEN,
    help='Shell to pipe commands to, default: /bin/bash -eux'
)
@cli2.option(
    'help', alias='h', color=cli2.GREEN,
    help='Output help for a job in sh.yml'
)
def run(path, job=None, **environment):
    """
    Render jobs defined in ./sh.yml or any sh.yml file.
    """
    if not os.path.exists(path):
        raise cli2.Cli2Exception(f'{path} does not exist')

    options = console_script.parser.options
    shell = options.get('shell', '/bin/bash -eux')

    schema = Schema()
    schema.parse(path)

    if options.get('help', False):
        yield schema[job].help
        return 0

    if job and job not in schema:
        yield '\n'.join([
            f'{cli2.RED}{job}{cli2.RESET} not found in'
        ] + list(schema.paths))
        # yield f'Listing jobs found in {cli2.RED}{path}{cli2.RESET}'
        job = None

    if not job:
        yield from ls(schema)
        return 0

    job = schema[job]

    if console_script.parser.options.get('debug', False):
        # generate from schema to support hooks
        yield from schema.script(job.name)
        return 0

    fd, path = tempfile.mkstemp(prefix='.shyml', dir='.')
    with open(path, 'w') as f:
        for line in schema.script(job.name):
            f.write(line + '\n')

    shell_arg = shell.split(' ') + [path]

    proc = subprocess.Popen(
        shell_arg,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    proc.communicate()
    os.unlink(path)
    return proc.returncode


def ls(schema, prefix=None):
    yield f'{LOGO} has found the following jobs:'
    yield ''

    if schema:
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
    else:
        yield f'No {cli2.RED}sh.yml{cli2.RESET} found !'

    yield f'''
Create a sh.yml with any number of YAML documents, each containing at least a
name string and a script string or list and/or env dict. Commit it in your
repository then you can run:

    shyml             {cli2.GREEN}show jobs in sh.yml{cli2.RESET}
    shyml [job] -d    {cli2.GREEN}output the job's shell script{cli2.RESET}
    shyml [job]       {cli2.YELLOW}execute the job's shell script{cli2.RESET}

Note that shyml jobs should call other jobs by calling the shyml command.
'''.strip()


def help(job):
    """
    Show help for a job.

    To get the list of jobs that you can get help for, run shyml without
    argument.
    """
    if job not in console_script.schema:
        return '\n'.join([
            f'{cli2.RED}{job}{cli2.RESET} not found in'
        ] + list(console_script.schema.paths))

    out = [
        ' '.join([
            'Showing help for',
            ''.join([
                cli2.GREEN,
                job,
                cli2.RESET,
            ]),
            'job from',
            ''.join([
                cli2.YELLOW,
                console_script.schema[job].path,
                cli2.RESET,
            ]),
        ]),
        console_script.schema[job].help,
        f'Output generated bash job:',
        f'{cli2.GREEN}shyml -d {job}{cli2.YELLOW}',
        '',
        f'Run the generated bash for this job:',
        f'{cli2.GREEN}shyml {job}{cli2.RESET}',
    ]
    return '\n'.join(out)


class ConsoleScript(cli2.ConsoleScript):
    def call(self, command):
        self.schema = Schema.cli()
        return super().call(command)

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
        env.update(console_script.parser.funckwargs)

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
    def __init__(self):
        self.hooks = {
            'before': [],
        }
        self.paths = []

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

    def parse(self, path):
        with open(path, 'r') as f:
            docs = [
                yaml.load(i, Loader=yaml.SafeLoader)
                for i in f.read().split('---') if i.strip()
            ]

        for doc in docs:
            if not doc:
                continue

            name = doc.get('name')
            job = self[name] = Job.factory(doc, self)
            job.path = path

            if job.hook:
                self.hooks[job.hook].append(job)

        for job in self.values():
            job.visit(self)

    @classmethod
    def cli(cls):
        paths = [
            'sh.yml',
            os.getenv('SHYML'),
            os.path.join(os.path.dirname(__file__), 'sh.yml'),
        ]

        self = cls()

        for path in paths:
            if not path:
                continue

            if path in self.paths:
                continue

            if not os.path.exists(path):
                continue

            self.parse(path)

        return self


console_script = cli2.ConsoleScript(
    __doc__,
    default_command='run'
).add_commands(run, help)
