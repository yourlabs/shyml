import pprint
import sys

from autoplay.schema import Schema
from autoplay.executor import get_executor

import clilabs
import clilabs.builtins


help = clilabs.builtins.help


def main(*args):
    '''
    Bash orchestrator for yaml.

    Lets you run a job or dryrun it, or do just the setup/script/clean stage of
    a job.

    Autoplay usage:

        autoplay
        autoplay describe [job]
        autoplay run [--dryrun] [job]
        autoplay setup [--dryrun] [job]
        autoplay script [--dryrun] [job]
        autoplay clean [--dryrun] [job]
    '''
    args, kwargs = clilabs.expand(*(args or sys.argv[:]))

    if len(args) > 2:
        jobs = args[2]
    else:
        jobs = None

    if len(args) > 1:
        command = args[1]
    else:
        command = None

    if not jobs:
        command = 'help'
    else:
        command = command or 'debug'

    schema = Schema.cli()

    if command == 'help':
        print('# Found jobs:')
        print('')
        for i in schema.keys():
            print(' -', i)
        print('')
        print('# Run autoplay describe [job] to see one of them')
        print('')
        print('# Generic help:')
        return clilabs.builtins.help('autoplay.cli')

    elif command == 'describe':
        for job in jobs.split(',') if jobs else []:
            pprint.pprint(schema[job])
        return

    elif command in ['setup', 'script', 'clean']:
        kwargs['stages'] = command

    strategy = get_executor(
        kwargs.pop('executor', 'linux')
    )(schema, **kwargs)

    for name in jobs.split(','):
        strategy.load_job(name)

    strategy()
    return strategy.wait()
