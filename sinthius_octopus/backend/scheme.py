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

X_NUC_ID = Argument('nuc_id', str, None, True)
X_NUC_LIST = Argument('nuc_list', list, None, True)
X_NAME = Argument('name', str, None, True)
X_IP = Argument('ip', str, None, True)
X_PORT = Argument('port', int, None, True)
X_MODE = Argument('mode', int, 0, False)

M_ADD = Method('add', '__add', (X_NAME, X_IP, X_PORT, X_MODE), None)
M_REMOVE = Method('remove', '__remove', (X_NUC_ID, X_IP, X_PORT), None)
M_LIST = Method('list', '__list', (X_NUC_LIST,), None)

__api__ = {'add': M_ADD, 'remove': M_REMOVE, 'list': M_LIST}


def api_reset():
    return deepcopy(__api__), tuple(__api__.keys())
