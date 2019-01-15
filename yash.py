"""
YaSH: The OBSCENE Bash orchestrator for yaml.
"""

import os
import pprint
import yaml

import cli2


def run(jobs=None, **kwargs):
    """
    Render jobs defined in ./yash.yml or any yash.yml file.
    """
    if not jobs:
        return ls()

    yield from console_script.schema.script(*jobs.split(','))


def ls():
    print('# Found jobs:')
    print('')
    for i in console_script.schema.keys():
        print(' -', i)
    print('')
    print('# Run autoplay describe [job] to see one of them')
    print('')


def describe(jobs):
    """ describe
    """
    for job in jobs.split(',') if jobs else []:
        pprint.pprint(console_script.schema[job])
    return


class ConsoleScript(cli2.ConsoleScript):
    def call(self, command):
        if command.name != 'help':
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

    def script(self, *jobs):
        for hook in self.hooks['before jobs']:
            yield from hook.script()

        for name in jobs:
            yield from self[name].script()

    def parse(self, path):
        with open(path, 'r') as f:
            docs = [yaml.load(i) for i in f.read().split('---')]

        for doc in docs:
            if not doc:
                continue

            name = doc.get('name')
            job = self[name] = Job.factory(doc, self)

            if job.hook:
                self.hooks[job.hook].append(job)

    @classmethod
    def cli(cls):
        paths = [
            name
            for name in (
                'yash.yml',
                os.getenv('YASH'),
                os.path.join(os.path.dirname(__file__), 'yash.yml'),
            )
            if name and os.path.exists(name)
        ]
        self = cls()
        for path in paths:
            self.parse(path)
        return self


console_script = ConsoleScript(
    __doc__,
    default_command='run'
).add_commands(run, describe)
