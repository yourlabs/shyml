import pprint
import sys

from autoplay.backend import Plays

import clilabs
import clilabs.builtins


help = clilabs.builtins.help


def main(*args, **environment):
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
    args = args or sys.argv[:]

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

    plays = Plays.cli(jobs.split(',') if jobs else [])

    if command == 'help':
        print('# Found jobs:')
        print('')
        for i in plays.schema.keys():
            print(' -', i)
        print('')
        print('# Run autoplay describe [job] to see one of them')
        print('')
        print('# Generic help:')
        return clilabs.builtins.help('autoplay.cli')

    elif command == 'describe':
        for job in jobs.split(',') if jobs else []:
            pprint.pprint(plays.schema[job])
        return

    elif command in ['setup', 'script', 'clean']:
        plays.stages = [command]

    if 'dryrun' in clilabs.context.args:
        plays.strategy = 'dryrun'

    return plays()
