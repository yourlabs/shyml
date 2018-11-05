import pkg_resources


def get_executor(executor_name):
    executors = pkg_resources.iter_entry_points('autoplay_executors')
    for entry in executors:
        if entry.name == executor_name:
            return entry.load()


class Executor:
    modes = ['run', 'dryrun']

    def __init__(self, schema, **options):
        self.command_count = 0
        self.job_count = 0
        self.environment = options
        self.exit_status = None
        self.mode = options.pop('mode', 'run')
        self.schema = schema
        self.stages = options.pop('stages', 'setup,script,clean').split(',')
        self.environment = options
        self.jobs = []
        self.job_names = []

    def load_job(self, name):
        self.job_names.append(name)
        self.jobs.append(self.get_commands(name))

    def get_commands(self, name):
        deps = self.schema[name].get('requires', [])
        dst_cmds = []
        for stage in self.stages:
            src_cmds = self.schema[name].get(stage, [])

            if not isinstance(src_cmds, list):
                src_cmds = [src_cmds]

            for dep in deps:
                deps_cmds = self.schema[dep].get(stage, [])
                if not isinstance(deps_cmds, list):
                    deps_cmds = [deps_cmds]
                src_cmds = deps_cmds + src_cmds

            for cmd in src_cmds:
                dst_cmds.append(cmd)

        return dst_cmds

    def __call__(self):
        if not getattr(self, '_init', False):
            self.init()
            self._init = True

        if self.job_count < len(self.jobs):
            self.job = self.jobs[self.job_count]
            getattr(self, self.mode)()
        else:
            self.clean()
        return self.return_value
