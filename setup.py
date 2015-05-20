#!/usr/bin/python

import setuptools

from sentry.openstack.common import setup

setuptools.setup(
    name='sentry',
    version='1.0',
    description='Alarm System for Openstack',
    author='Netease',
    author_email='nvs@corp.netease.com',
    packages=setuptools.find_packages(exclude=['bin']),
    include_package_data=True,
    cmdclass=setup.get_cmdclass(),
    install_requires=setup.parse_requirements(),
    dependency_links=setup.parse_dependency_links(),
    classifiers=[
        'Development Status :: 1 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Environment :: No Input/Output (Daemon)',
    ],
    entry_points={
        'console_scripts': [
            'sentry-manage = sentry.cmd.manage:main',
            'sentry-api = sentry.cmd.api:main',
            'sentry-statsd = sentry.statsd.server:main',
            'sentry = sentry.cmd.server:main',
        ]
    },
    py_modules=[],
)
