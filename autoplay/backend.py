import os
import yaml

from clilabs import context


class Command:
    def __init__(self, shell):
        self.shell = shell

    @classmethod
    def factory(cls, orchestrator, name):
        self = cls()
        self.orchestrator = orchestrator
        self.name = name
        self.job = orchestrator.jobs[name]
        return self

    def __call__(self):
        self.shell.send('(' + instruction +
                       ' && echo CLILABS_AUTO_DONE_TOKEN )' +
                       ' || echo $? CLILABS_AUTO_ERR_TOKEN')


class Play:
    pass


class Context:
    pass


class Jobs(dict):
    def parse(self, path):
        with open(path, 'r') as f:
            docs = [yaml.load(i) for i in f.read().split('---')]

        for doc in docs:
            if not doc:
                continue

            name = doc.get('name', 'default')
            if name in self:
                continue

            doc['_path'] = path
            self[name] = doc

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


class Orchestrator:
    @classmethod
    def factory(cls, *names, **kwargs):
        obj = cls()
        obj.jobs = Jobs.cli()
        obj.cmds = [
            Command.factory(obj, name)
            for name in names
        ]
        return obj

    def __call__(self):
        self.proc = ProcessController()
        proc.run(['bash', '-eux'], {
            'detached': True,
            'private': True,
            'echo': False,
            'when': [
                ['^CLILABS_AUTO_JOB_COMPLETE_TOKEN$', self.next_job],
                ['(?!^([0-9]* )?CLILABS_AUTO_.*_TOKEN$)', self.print_line],
                ['^CLILABS_AUTO_DONE_TOKEN$', self.next_cmd],
                ['^.*CLILABS_AUTO_ERR_TOKEN$', self.abort],
            ]
        })
        for cmd in obj.cmds:
            cmd()
