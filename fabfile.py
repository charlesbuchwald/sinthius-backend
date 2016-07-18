#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:20
# ~

from fabric.api import local

_SERVER = 'PYTHONPATH=$PYTHONPATH:{path} python -m {module} --port={port} ' \
          '--nuc_port={port} --debug={debug}'
_PATH = '/Volumes/Projects/library/python/2.7:/Volumes/Projects/library' \
        '/python/envs/dev/lib/python2.7/site-packages'


def run_nuc_8041():
    local(_SERVER.format(path=_PATH, port=8041, module='sinthius_octopus.run'))


def run_nuc_8042():
    local(_SERVER.format(path=_PATH, port=8042, module='sinthius_octopus.run'))


def run_nuc_8043():
    local(_SERVER.format(path=_PATH, port=8043, module='sinthius_octopus.run'))


def run_nuc_8044():
    local(_SERVER.format(path=_PATH, port=8044, module='sinthius_octopus.run'))

def run_nuc_8045():
    local(_SERVER.format(path=_PATH, port=8045, module='sinthius_octopus.run'))

def run_nuc(port, debug=False):
    local(_SERVER.format(path=_PATH, port=port, module='sinthius_octopus.run',
                         debug=debug))