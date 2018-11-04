'''Autoplay usage:

    autoplay help [command]
    autoplay debug [job]
    autoplay run [job]
    autoplay setup [job]
'''
import sys

from autoplay.backend import Orchestrator

import clilabs
import clilabs.builtins


help = clilabs.builtins.help


def cli(*argv):
    argv = sys.argv[1:] or ['help', 'autoplay']
    cb = clilabs.modfuncimp(*clilabs.funcexpand(argv[0], 'autoplay'))
    args, kwargs = clilabs.expand(*argv[1:])
    return cb(*args, **kwargs)


def play(*names, **kwargs):
    return Orchestrator.factory(*names, **kwargs)()


def debug(*args, jobs=None, **kwargs):
    """Dry run of auto:play

    This function will only show what would have been done by the play function
    See play for more information:

    autoplay
    """
    _execute.debug = True
    return _execute(jobs, kwargs)
