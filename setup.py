#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:09
# ~

from setuptools import setup, find_packages
from sinthius import version

with open('README.rst', 'r') as f:
    long_description = f.read()

requires = [line.strip() for line in open('requirements.txt', 'r')]

entry_points = '''
[console_scripts]
octopus=sinthius_octopus.cli:main
'''



setup(
    name='sinthius-backend',
    version=version,
    url='',
    license='MIT',
    author='Alejandro M. Bernardis',
    author_email='alejandro.m.bernardis@gmail.com',
    description='SINTHIUS, is a BaaS Framework written in Python.',
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Natural Language :: Spanish',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ],
    zip_safe=False,
    install_requires=requires,
    include_package_data=True,
    packages=find_packages(),
    package_dir={
        'sinthius': 'sinthius',
        'sinthius_octopus': 'sinthius_octopus'
    },
    platforms=[
        'Linux'
    ],
    entry_points=entry_points
)

