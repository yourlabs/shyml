import pprint
import sys

from autoplay.schema import Schema
from autoplay.strategy import get_strategy

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

    try:
        jobs = args[2]
    except IndexError:
        jobs = None

    try:
        command = args[1]
    except IndexError:
        command = None

    if not jobs and not command:
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

    strategy = get_strategy(
        kwargs.pop('strategy', 'local')
    )(schema, **kwargs)

    for name in jobs.split(','):
        strategy.load_job(name)

    return strategy()
