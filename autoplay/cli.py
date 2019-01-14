'''
Autoplay

Bash orchestrator for yaml.

Lets you run a job or dryrun it

Autoplay usage:

    autoplay
    autoplay ls
    autoplay describe [job]
    autoplay run [--dryrun] [job]
'''

import pprint

from autoplay.schema import Schema
from autoplay.executor import get_executor

import cli2


@cli2.option('dryrun', color=cli2.GREEN, help='Dry run the job')
@cli2.option('executor', help='Executor type (linux, venv, docker)')
@cli2.option('strategy', help='Strategy to user (serial, parrallele)')
def run(jobs=None):
    ''' run
    '''
    if not jobs:
        return ls()

    executor = get_executor(
        console_script.parser.options.get('executor', 'linux')
    )

    if console_script.parser.options.get('dryrun', False):
        mode = 'dryrun'
    else:
        mode = 'run'

    strategy = executor(console_script.schema, **{
        'mode': mode,
        'strategy': console_script.parser.options.get('strategy', 'serial'),
    })

    for name in jobs.split(','):
        strategy.load_job(name)


    strategy()
    return strategy.wait()


def ls():
    print('# Found jobs:')
    print('')
    for i in console_script.schema.keys():
        print(' -', i)
    print('')
    print('# Run autoplay describe [job] to see one of them')
    print('')


def describe(jobs):
    ''' describe
    '''
    for job in jobs.split(',') if jobs else []:
        pprint.pprint(console_script.schema[job])
    return


class ConsoleScript(cli2.ConsoleScript):
    def call(self, command):
        if command.name != 'help':
            self.schema = Schema.cli()
        return super().call(command)


console_script = ConsoleScript(
        __doc__,
        default_command='run'
    ).add_commands(run, describe)
