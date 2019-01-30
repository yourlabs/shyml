"""
ShYml: The OBSCENE Bash orchestrator for yaml.
"""

import os
import yaml

import colorama
import cli2


LOGO = f'{cli2.GREEN}Sh{cli2.YELLOW}Y{cli2.RED}ml{cli2.RESET}'


def run(jobs=None, **kwargs):
    """
    Render jobs defined in ./sh.yml or any sh.yml file.
    """
    if jobs:
        yield from console_script.schema.script(*jobs.split(','))
    else:
        yield from ls()


def ls():
    yield f'{LOGO} has found the following jobs:'
    yield ''

    if console_script.schema:
        width = len(max(console_script.schema.keys(), key=len)) + 1
        for name, job in console_script.schema.items():
            line = ' ' + ''.join([
                job.color_code,
                name,
                cli2.RESET,
                (width - len(name)) * ' ',
                job.help.split('\n')[0]
            ])
            yield line
        yield ''
    else:
        yield f'No {cli2.RED}sh.yml{cli2.RESET} found !'

    yield 'Usage:'
    yield ''.join([
        cli2.GREEN,
        'shyml [job]',
        cli2.RESET,
        '               ',
        'to generate the shell script.',
    ])
    yield ''.join([
        cli2.GREEN,
        'shyml [job] | bash -eux',
        cli2.RESET,
        '   ',
        'to execute the shell script in bash.',
    ])


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
        f'To see the generated bash for this job, just run:',
        f'{cli2.GREEN}shyml {job}{cli2.RESET}',
        '',
        f'To execute this job, you can pipe it to a shell like bash ie.:',
        f'{cli2.GREEN}shyml {job}{cli2.YELLOW} | bash -eux{cli2.RESET}',
    ]
    return '\n'.join(out)


class ConsoleScript(cli2.ConsoleScript):
    def call(self, command):
        self.schema = Schema.cli()
        return super().call(command)


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

    def script(self):
        env = dict()
        for name in self.requires:
            if self.schema[name].env:
                env.update(self.schema[name].env)
        env.update(self.env)
        env.update(console_script.parser.funckwargs)

        for key, value in env.items():
            yield ''.join(['export ', str(key), '=', str(value)])

        for name in self.requires:
            yield from self.schema[name].script()

        script = self.get('script')
        if not isinstance(script, list):
            script = [script]

        for chunk in script:
            yield chunk


class Schema(dict):
    def __init__(self):
        self.hooks = {
            'before jobs': [],
        }
        self.paths = []

    def script(self, *jobs):
        for hook in self.hooks['before jobs']:
            yield from hook.script()

        for name in jobs:
            yield from self[name].script()

    def parse(self, path):
        with open(path, 'r') as f:
            docs = [yaml.load(i) for i in f.read().split('---') if i.strip()]

        for doc in docs:
            if not doc:
                continue

            name = doc.get('name')
            job = self[name] = Job.factory(doc, self)
            job.path = path

            if job.hook:
                self.hooks[job.hook].append(job)

    @classmethod
    def cli(cls):
        paths = [
            'sh.yml',
            os.getenv('YASH'),
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


console_script = ConsoleScript(
    __doc__,
    default_command='run'
).add_commands(run, help)
