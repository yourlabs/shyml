"""
YaSH: The OBSCENE Bash orchestrator for yaml.
"""

import collections
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

    env = collections.OrderedDict()
    env.update(console_script.schema.environment)

    for job in jobs.split(','):
        env.update(console_script.parser.funckwargs)

        for key, value in env.items():
            yield ''.join(['export ', str(key), '=', str(value)])

        for line in console_script.schema[job].get('script', []):
            yield line


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


class Schema(dict):
    def __init__(self):
        self.environment = dict()

    def parse(self, path):
        with open(path, 'r') as f:
            docs = [yaml.load(i) for i in f.read().split('---')]

        for doc in docs:
            if not doc:
                continue

            if 'name' not in doc:
                for key, value in doc.get('env', {}).items():
                    self.environment.setdefault(key, value)
            else:
                self[doc['name']] = doc

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
