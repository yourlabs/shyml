import os
import re
import shlex
import shutil
import pty
import yaml

from processcontroller import ProcessController


class Schema(dict):
    def parse(self, path):
        self.shells = dict()
        self.environment = dict()
        self.variables = dict()

        with open(path, 'r') as f:
            docs = [yaml.load(i) for i in f.read().split('---')]

        for doc in docs:
            if not doc:
                continue

            doc['_path'] = path
            parser = doc.get('_parser', 'job')
            getattr(self, f'parse_{parser}')(doc)

    def parse_job(self, doc):
        for key, value in doc.items():
            if key.startswith('_'):
                continue

            if isinstance(value, str) or isinstance(value, int):
                self.environment.setdefault(key, value)

        name = doc.get('name', 'default')
        if name not in self:
            self[name] = doc

    def parse_globals(self, doc):
        for key, value in doc.items():
            if key.startswith('_'):
                continue

            if isinstance(value, str) or isinstance(value, int):
                var = self.environment
            else:
                var = self.variables

            var.setdefault(key, value)

    @classmethod
    def cli(cls):
        paths = [
            name
            for name in (
                'autoplay.yml',
                os.getenv('AUTOPLAY_PATH'),
                os.path.join(os.path.dirname(__file__), 'autoplay.yml'),
            )
            if name and os.path.exists(name)
        ]
        self = cls()
        for path in paths:
            self.parse(path)
        return self


class Command:
    def __init__(self, line, proc):
        self.line = line
        self.proc = proc

    def __call__(self):
        self.proc.send('(' + command +
                       ' && echo AUTOPLAY_DONE_TOKEN )' +
                       ' || echo $? AUTOPLAY_ERR_TOKEN')


class Play(list):
    @classmethod
    def cli(cls, name, plays):
        self = cls()

        for i in plays.stages:
            val = plays.schema[name].get(i, [])

            if not isinstance(val, list):
                val = [val]
            for cmd in val:
                self.append(Command(cmd, plays))

        return self

    def next_job(self):
        for cmd in self:
            if not cmd.done:
                return cmd

    def __call__(self):
        for cmd in self:
            if not cmd.done:
                return cmd()


class Plays(list):
    def __init__(self):
        self.play_count = 0
        self.command_count = 0
        self.exit_status = None
        self.stages = ['setup', 'script', 'clean']
        self.environment = {}
        self.shell = '/bin/bash -eu'
        self.strategy = 'exec'

    @classmethod
    def cli(cls, jobs):
        self = cls()
        self.schema = Schema.cli()
        for name in jobs:
            self.append(Play.cli(name, self))
        return self

    def send(self, line, linetoprint=None):
        if self.strategy == 'dryrun':
            print(linetoprint or line)

        else:
            if linetoprint:
                print(linetoprint)
                self.proc.options['echo'] = False

            self.proc.send(line)

            if linetoprint:
                self.proc.options['echo'] = True

    @property
    def proc(self):
        cached = getattr(self, '_proc', None)
        if not cached:
            cached = self._proc = ProcessController()
            self._proc.run(self.shell.split(' '), {
                'detached': True,
                'private': True,
                'echo': self.strategy != 'dryrun',
                'when': [
                    ['^AUTOPLAY_JOB_COMPLETE_TOKEN$', self.next_job],
                    ['(?!^([0-9]* )?AUTOPLAY_.*_TOKEN$)', self.print_line],
                    ['^AUTOPLAY_DONE_TOKEN$', self.next_cmd],
                    ['^.*AUTOPLAY_ERR_TOKEN$', self.abort],
                ]
            })
        return cached

    def __call__(self):
        print(f'# Starting with strategy: {self.strategy}')
        for key, value in self.environment.items():
            self.send(f'export {key}="{value}"')

        for key, value in self.schema.environment.items():
            if key in self.environment:
                continue
            self.send(f'export {key}="{value}"')

        if self.play_count < len(self):
            self.play = self[self.play_count]

            if self.strategy == 'dryrun':
                self.dryrun()
            else:
                self.run()
        else:
            self.proc.close()

        return self.proc.return_value

    def dryrun(self):
        for cmd in self.play:
            print(cmd.line)

    def run(self):
        if self.command_count < len(self.play):
            command = self.play[self.command_count]
            self.send('(' + command.line +
                      ' && echo AUTOPLAY_DONE_TOKEN )' +
                      ' || echo $? AUTOPLAY_ERR_TOKEN',
                      command.line)
        else:
            if self.exit_status is None:
                self.exit_status = 0
            self.send('echo AUTOPLAY_JOB_COMPLETE_TOKEN')

    def next_job(self):
        self.play_count = 0
        self.command_count += 1
        self()

    def next_cmd(self, c, l):
        self.command_count += 1
        self()

    def abort(self, c, l):
        self.command_count = len(self.play)
        self.exit_status = None

    def print_line(self, c, l):
        os.write(pty.STDOUT_FILENO, l.encode())
