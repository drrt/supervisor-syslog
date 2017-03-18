#!/usr/bin/env python

from setuptools import setup

setup(name='supervisor-syslog',
    version='0.1.0',
    description='supervisor event handler for syslogging',
    packages=['supervisor_syslog'],
    setup_requires=['pytest-runner'],
    install_requires=['PyYAML>=3.0'],
    tests_require=['pytest'],
    entry_points={'console_scripts': ['supervisor-syslog=supervisor_syslog:handler']}
    )

