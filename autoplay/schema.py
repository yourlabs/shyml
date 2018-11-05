import os
import yaml


class Schema(dict):
    def parse(self, path):
        self.shells = dict()
        self.environment = dict()
        self.plugins = dict()

        with open(path, 'r') as f:
            docs = [yaml.load(i) for i in f.read().split('---')]

        for doc in docs:
            if not doc:
                continue

            env = doc.get('env', {})
            if 'name' not in doc:
                for key, value in env.items():
                    self.environment.setdefault(key, value)
            else:
                self[doc['name']] = doc

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
