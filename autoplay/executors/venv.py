from autoplay.executors.linux import Linux

import venv


class Virtualenv(Linux):
    def proc_init(self):
        env = venv.EnvBuilder(
            system_site_packages=self.environment.pop(
                'venv_system_site_packages', False),
            clear=self.environment.pop(
                'venv_clear', False),
            symlinks=self.environment.pop(
                'venv_symlinks', False),
            upgrade=self.environment.pop(
                'venv_upgrade', True),
            with_pip=self.environment.pop(
                'venv_with_pip', True),
        )

        path = self.environment.pop('venv_path', 'venv')
        env.create(path)
        self.send(f'export PATH={path}/bin:$PATH')
        super().proc_init()
