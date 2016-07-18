#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:28
# ~

from sinthius import compat
from sinthius.utils.decorators import try_or_false


class ObjectVersion(object):
    def __init__(self, version=None):
        if not isinstance(version, compat.string_type):
            raise TypeError('The version value, must be a string')
        self._version = version.lower()
        self._components = version.split('.')

    @property
    def value(self):
        return self._version

    @property
    def components(self):
        return self._components

    def is_valid(self):
        if not self._version \
                or not self._components\
                or len(self._components) < 2:
            return False
        return True

    @try_or_false
    def lt(self, version):
        return cmp(self._components, version.split('.')) < 0

    @try_or_false
    def le(self, version):
        return cmp(self._components, version.split('.')) <= 0

    @try_or_false
    def eq(self, version):
        return cmp(self._components, version.split('.')) == 0

    @try_or_false
    def gt(self, version):
        return cmp(self._components, version.split('.')) > 0

    @try_or_false
    def ge(self, version):
        return cmp(self._components, version.split('.')) >= 0
