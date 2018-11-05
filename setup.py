from setuptools import setup

setup(
    name='autoplay',
    versioning='distance',
    url='https://yourlabs.io/oss/autoplay',
    setup_requires='setupmeta',
    keywords='automation cli',
    entry_points={
        'console_scripts': [
            'autoplay = autoplay.cli:main',
        ],
        'autoplay_executors': [
            'linux = autoplay.executors.linux:Linux',
            'docker = autoplay.executors.docker:Docker',
            'venv = autoplay.executors.venv:Virtualenv',
        ],
    },
    install_requires=['clilabs', 'processcontroller'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Plugins',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Database',
        'Topic :: Software Development',
        'Topic :: System',
        'Topic :: Terminals',
    ],
    python_requires='>=3',
)
