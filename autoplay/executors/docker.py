from autoplay.executor import Executor

import docker


class Docker(Executor):
    def init(self):
        self.client = docker.from_env()
        self.container = self.client.containers.run(
            self.options.get('docker_image', 'alpine'),
            detach=True,
        )

    def run(self):
        self.return_value = 0
