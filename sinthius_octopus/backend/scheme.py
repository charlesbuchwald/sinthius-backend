#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 18/Jun/2016 22:09
# ~

from copy import deepcopy
from collections import namedtuple

Method = namedtuple('Method', ['name', 'method', 'arguments', 'description'])
Argument = namedtuple('Argument', ['name', 'type', 'default', 'required'])

X_NAME = Argument('name', str, None, True)
X_NODE = Argument('node', str, None, True)
X_DATA = Argument('data', str, None, True)
X_IP = Argument('ip', str, None, True)
X_PORT = Argument('port', int, None, True)

__api__ = {
    'CHANGE': Method('change', '_on_change', (X_NODE, X_DATA), None)
}


def api_reset():
    return deepcopy(__api__), tuple(__api__.keys())
