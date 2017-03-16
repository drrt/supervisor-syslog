#!/usr/bin/env python

from setuptools import setup

setup(name='sypervisor-syslog',
    version='0.1.0',
    description='supervisor event handler for syslogging',
    packages=['supervisor_syslog'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    entry_points={'console_scripts': ['supervisor-syslog=supervisor_syslog:handler']}
    )

