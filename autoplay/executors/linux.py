import os
import pty

from autoplay.executor import Executor

from processcontroller import ProcessController


class Linux(Executor):
    def __init__(self, schema, **options):
        super().__init__(schema, **options)
        self.exit_status = 0
        self.shell = '/bin/bash -eu'

    def wait(self):
        if self.mode == 'dryrun':
            return True
        pid, retcode = self.proc.wait()
        if self.exit_status:
            return self.exit_status
        else:
            return retcode

    def clean(self):
        return self.proc.close()

    @property
    def return_value(self):
        return self.proc.return_value

    @property
    def proc(self):
        proc = getattr(self, '_proc', None)
        if not proc:
            proc = self._proc = ProcessController()
            proc.run(self.shell.split(' '), {
                'detached': True,
                'private': True,
                'echo': self.mode != 'dryrun',
                'decode': False,
                'when': [
                    ['^AUTOPLAY_JOB_COMPLETE_TOKEN$', self.next_job],
                    ['(?!^([0-9]* )?AUTOPLAY_.*_TOKEN$)', self.print_line],
                    ['^AUTOPLAY_DONE_TOKEN$', self.next_cmd],
                    ['^.*AUTOPLAY_ERR_TOKEN$', self.abort],
                ]
            })

        return proc

    def init(self):
        for key, value in self.environment.items():
            self.send(f'export {key}="{value}"')

        for key, value in self.schema.environment.items():
            if key in self.environment:
                continue
            self.send(f'export {key}="{value}"')

        for key, value in self.doc.get('env', {}).items():
            self.send(f'export {key}="{value}"')

    def send(self, line, linetoprint=None):
        if self.mode == 'dryrun':
            print(linetoprint or line)

        else:
            if linetoprint is not None:
                if linetoprint != '':
                    print(linetoprint)
                self.proc.options['echo'] = False

            self.proc.send(line)

            if linetoprint is not None:
                self.proc.options['echo'] = True

    def dryrun(self):
        for job in self.jobs:
            for cmd in job:
                print(cmd)

    def run(self):
        if self.command_count < len(self.job):
            command = self.job[self.command_count]
            self.send('((' + command + ')' +
                      ' && echo AUTOPLAY_DONE_TOKEN )' +
                      ' || echo $? AUTOPLAY_ERR_TOKEN',
                      linetoprint=command
                      )
        else:
            if self.exit_status is None:
                self.exit_status = 0
            self.send('echo AUTOPLAY_JOB_COMPLETE_TOKEN', '')
        print()
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
        os.write(pty.STDOUT_FILENO, l)
