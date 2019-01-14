import os
import pty
import time

from autoplay.executor import Executor

from processcontroller import ProcessController


class Linux(Executor):
    def __init__(self, schema, **options):
        super().__init__(schema, **options)
        self.exit_status = 0
        self.prompt = os.environ['PS1'] = 'AUTOPLAY_PROMPT_HACK'
        self.first_prompt = True
        self.shell = '/bin/bash -eu'
        self._proc = None

    def wait(self):
        pid, retcode = self.proc.wait()
        return self.exit_status

    def clean(self):
        return self.proc.close()

    @property
    def proc(self):
        if not self._proc:
            self._proc = ProcessController()
            self._proc.run(self.shell.split(' '), {
                'detached': True,
                'private': True,
                'echo': False,
                'decode': False,
                'when': [
                    ['^AUTOPLAY_JOB_COMPLETE_TOKEN\r?\n$', self.next_job],
                    ['^AUTOPLAY_DONE_TOKEN\r?\n$', self.next_cmd],
                    ['^[0-9]+ AUTOPLAY_ERR_TOKEN\r?\n$', self.abort],
                    [
                        '^(?!^([0-9]* )?AUTOPLAY_.*_TOKEN\r?\n$)',
                        self.print_line
                    ],
                ]
            })
            self._proc.send(f'export PS1="{self.prompt}"')
            while self.first_prompt:
                time.sleep(0.5)
                self._proc.send('')
        return self._proc

    def init(self):
        envvars = getattr(self.schema, 'environment', {})
        envvars.update(getattr(self, 'environment', {}))
        envvars.update(self.doc.get('env', {}))
        added = []

        for key, value in envvars.items():
            if key not in added:
                added += key
                line = f'export {key}="{value}"'
                self.send(line, line)

    def send(self, line, linetoprint=None):
        proc = self.proc

        if linetoprint and linetoprint != '':
            os.write(pty.STDOUT_FILENO, b'$> ' + linetoprint.encode() + b'\n')
        proc.send(line)

    def dryrun(self):
        for job in self.jobs:
            for cmd in job:
                print(cmd)
        self.job_count = len(self.jobs)
        self()

    def run(self):
        if self.command_count < len(self.job):
            command = self.job[self.command_count]
            self.send('{ { ' + command + '; }' +
                      ' && echo AUTOPLAY_DONE_TOKEN; }' +
                      ' || echo $? AUTOPLAY_ERR_TOKEN',
                      linetoprint=command
                      )
        else:
            if self.exit_status is None:
                self.exit_status = 0
            self.send('echo AUTOPLAY_JOB_COMPLETE_TOKEN', '')
        return self.exit_status

    @property
    def doc(self):
        if self.job_count < len(self.job_names):
            return self.schema[self.job_names[self.job_count]]
        else:
            return {}

    def next_job(self, c, l):
        self.command_count = 0
        self.job_count += 1
        for key, value in self.doc.get('env', {}).items():
            self.send(f'export {key}="{value}"')
        self()

    def next_cmd(self, c, l):
        self.command_count += 1
        self()

    def abort(self, c, l):
        self.command_count = len(self.job)
        self.job_count = len(self.jobs)
        retcode, token = l.split(b' ')
        self.exit_status = int(retcode)
        self.proc.return_value = (self.proc.pid, self.exit_status)
        self()

    def print_line(self, c, l):
        if self.first_prompt:
            if l.decode().endswith(self.prompt + '\r\n'):
                self.first_prompt = False
        elif self.prompt not in l.decode():
            os.write(pty.STDOUT_FILENO, l)
