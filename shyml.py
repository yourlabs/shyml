"""
Orchestrate shell script units from a single sh.yml file.
"""

import cli2
import os
import shlex
import subprocess
import sys
import tempfile
import yaml


LOGO = f'{cli2.c.green}Sh{cli2.c.yellow}Y{cli2.c.red}ml{cli2.c.reset}'


class ConsoleScript(cli2.Group):
    def run(self, *args):
        fd, path = tempfile.mkstemp(prefix='.shyml', dir='.')
        with open(path, 'w') as f:
            f.write(self.schema.script(self.current))

        shell = os.getenv('shell', '/bin/bash -eux')
        shell_arg = shell.split(' ') + [path]

        # 1337 ArGv InJeC710n H4ck: proxying argv from: shyml sh.yml JOB foobar
        # And: proxying argv from: ./sh.yml JOB foobar
        # Will cause $1 to be "foobar" in the script content of JOB
        shell_arg += list(args)

        proc = subprocess.Popen(
            shell_arg,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        proc.communicate()
        os.unlink(path)
        sys.exit(proc.returncode)

    def help(self, *args, **kwargs):
        if args and args[0] in self.schema:
            return self.schema[args[0]].help
        return super().help(*args, **kwargs)

    def debug(self, name):
        return self.schema[name].script()

    def __call__(self, *argv):
        if not argv:
            print('Missing path to sh.yml argument')
            sys.exit(1)

        if not os.path.exists(argv[0]):
            print('File not found: ' + argv[0])
            sys.exit(1)

        self.add(self.help, doc='Show help for command')
        self.add(self.debug, doc='Show script for command')

        self.schema = Schema.factory(argv[0])
        for name, job in self.schema.items():
            self.add(self.run, name=name, doc=job.help)
        if len(argv) > 1:
            self.current = argv[1]
        argv = argv[1:]
        return super().__call__(*argv)


cli = ConsoleScript(__doc__)


class Job(dict):
    @classmethod
    def factory(cls, doc, schema):
        job = cls(doc)
        job.doc = doc
        job.schema = schema
        job.name = doc['name']
        job.hook = doc.get('hook', None)
        job.env = doc.get('env', {})
        job.requires = doc.get('requires', doc.get('require', []))
        if isinstance(job.requires, str):
            job.requires = [job.requires]
        job.help = doc.get('help', '')
        job.color = doc.get('color', 'yellow')
        job.color_code = getattr('cli2.c', job.color.upper(), cli2.c.reset)
        return job

    def visit(self, schema):
        self.parent = None
        self.children = []

        for job in schema.values():
            if job is self:
                continue

            if job.name.startswith(self.name):
                self.children.append(job)

            if self.name.startswith(job.name):
                if not self.parent:
                    self.parent = job
                elif len(self.parent.name) < job.name:
                    self.parent = job

    def script(self):
        out = []
        env = dict()
        for name in self.requires:
            if self.schema[name].env:
                env.update(self.schema[name].env)
        env.update(self.env)

        for key, value in env.items():
            out.append(''.join([
                'export ', str(key), '=', shlex.quote(str(value))
            ]))

        for name in self.requires:
            out.append('shyml_' + name)

        script = self.get('script')
        if not script:
            return

        if not isinstance(script, list):
            script = [l for l in script.split('\n') if l.strip()]

        for chunk in script:
            if chunk:
                out.append(chunk)
        return '\n'.join(out)


class Schema(dict):
    def __init__(self, path):
        self.hooks = {
            'before': [],
        }
        self.path = path

    def script(self, *jobs):
        out = []
        for job in self.values():
            out.append('shyml_' + job.name + '() {')
            if job.help:
                for line in job.help.strip().split('\n'):
                    out.append(f'    # {line}')
            out.append(self[job.name].script().replace('\n', '    \n'))
            out.append('}')

        for hook in self.hooks['before']:
            if hook.name == jobs[0]:
                continue
            out.append('shyml_' + hook.name)

        for name in jobs:
            if name not in self:
                out.append(''.join([
                    cli2.c.red,
                    'Job not found: ',
                    cli2.c.reset,
                    name,
                    '\n',
                    cli2.c.green,
                    'Job founds:',
                    cli2.c.reset,
                    '\n',
                    '\n'.join([f'- {i}' for i in sorted(self.keys())]),
                ]))
                sys.exit(1)
            out.append('shyml_' + name + ' "$@"')

        return '\n'.join(out)

    def parse(self):
        with open(self.path, 'r') as f:
            docs = [
                yaml.load(i, Loader=yaml.SafeLoader)
                for i in f.read().split('---') if i.strip()
            ]

        for doc in docs:
            if not doc:
                continue

            name = doc.get('name')
            job = self[name] = Job.factory(doc, self)

            if job.hook:
                self.hooks[job.hook].append(job)

        for job in self.values():
            job.visit(self)

    @classmethod
    def factory(cls, path=None):
        path = path or os.getenv('SHYML', 'sh.yml')

        self = cls(path)
        if not os.path.exists(path):
            print(f'{cli2.c.red}Could not find{cli2.c.reset} {path}')
        else:
            self.parse()

        return self
