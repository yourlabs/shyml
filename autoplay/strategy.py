import pkg_resources

from processcontroller import ProcessController


def get_strategy(strategy_name):
    strategies = pkg_resources.iter_entry_points('autoplay_strategies')
    for entry in strategies:
        if entry.name == strategy_name:
            return entry.load()


class Strategy:
    def __init__(self, schema, **options):
        self.command_count = 0
        self.job_count = 0
        self.environment = {}
        self.exit_status = None
        self.mode = options.pop('mode', 'run')
        self.schema = schema
        self.stages = options.pop('stages', 'setup,script,clean').split(',')
        self.environment = options
        self.jobs = []

    def load_job(self, name):
        self.jobs.append(self.get_commands(name))

    def get_commands(self, name):
        dst_cmds = []
        for stage in self.stages:
            src_cmds = self.schema[name].get(stage, [])

            if not isinstance(src_cmds, list):
                src_cmds = [src_cmds]

            for cmd in src_cmds:
                dst_cmds.append(cmd)

        return dst_cmds


class Local(Strategy):
    def __init__(self, schema, **options):
        super().__init__(schema, **options)
        self.shell = '/bin/bash -eu'

    def __call__(self):
        if self.job_count < len(self.jobs):
            self.job = self.jobs[self.job_count]

            if self.mode == 'dryrun':
                self.dryrun()
            else:
                self.run()
        else:
            self.proc.close()

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
                'when': [
                    ['^AUTOPLAY_JOB_COMPLETE_TOKEN$', self.next_job],
                    ['(?!^([0-9]* )?AUTOPLAY_.*_TOKEN$)', self.print_line],
                    ['^AUTOPLAY_DONE_TOKEN$', self.next_cmd],
                    ['^.*AUTOPLAY_ERR_TOKEN$', self.abort],
                ]
            })

            for key, value in self.environment.items():
                self.send(f'export {key}="{value}"')

            for key, value in self.schema.environment.items():
                if key in self.environment:
                    continue
                self.send(f'export {key}="{value}"')

        return proc

    def send(self, line, linetoprint=None):
        if self.mode == 'dryrun':
            print(linetoprint or line)

        else:
            if linetoprint:
                print(linetoprint)
                self.proc.options['echo'] = False

            self.proc.send(line)

            if linetoprint:
                self.proc.options['echo'] = True

    def dryrun(self):
        for job in self.jobs:
            for cmd in job:
                print(cmd)

    def run(self):
        if self.command_count < len(self.job):
            command = self.job[self.command_count]
            self.send('(' + command +
                      ' && echo AUTOPLAY_DONE_TOKEN )' +
                      ' || echo $? AUTOPLAY_ERR_TOKEN',
                      )
        else:
            if self.exit_status is None:
                self.exit_status = 0
            self.send('echo AUTOPLAY_JOB_COMPLETE_TOKEN')
        pid, status = self.proc.wait()
        print()
        return self.proc.return_value or 0

    def next_job(self):
        self.command_count = 0
        self.job_count += 1
        self()

    def next_cmd(self, c, l):
        self.command_count += 1
        self()

    def abort(self, c, l):
        self.command_count = len(self.play)
        self.exit_status = None

    def print_line(self, c, l):
        os.write(pty.STDOUT_FILENO, l.encode())


class Docker(Strategy):
    pass


class Virtualenv(Strategy):
    pass
