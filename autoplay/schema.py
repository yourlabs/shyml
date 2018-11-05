import os
import yaml


class Schema(dict):
    def parse(self, path):
        self.shells = dict()
        self.environment = dict()
        self.variables = dict()
        self.plugins = dict()

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
