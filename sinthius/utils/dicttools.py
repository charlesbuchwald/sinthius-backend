#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:27
# ~

from sinthius.utils.decorators import dict_or_raise


class DotDict(dict):
    def __init__(self, value=None):
        if value is None:
            pass
        elif isinstance(value, dict):
            for key in value:
                self.__setitem__(key, value[key])
        else:
            raise TypeError('Can only initialize "DotDict" from another dict')

    def __setitem__(self, key, value):
        if '.' in key:
            my_key, rest_of_key = key.split('.', 1)
            target = self.setdefault(my_key, DotDict())
            if not isinstance(target, DotDict):
                raise KeyError('Cannot set "%s" in "%s" (%s)'
                               % (rest_of_key, my_key, repr(target)))
            target[rest_of_key] = value
        else:
            if isinstance(value, dict) and not isinstance(value, DotDict):
                value = DotDict(value)
            dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        if '.' not in key:
            return dict.__getitem__(self, key)
        my_key, rest_of_key = key.split('.', 1)
        target = dict.__getitem__(self, my_key)
        if not isinstance(target, DotDict):
            raise KeyError('Cannot get "%s" in "%s" (%s)'
                           % (rest_of_key, my_key, repr(target)))
        return target[rest_of_key]

    def __contains__(self, key):
        if '.' not in key:
            return dict.__contains__(self, key)
        my_key, rest_of_key = key.split('.', 1)
        if not dict.__contains__(self, my_key):
            return False
        target = dict.__getitem__(self, my_key)
        if not isinstance(target, DotDict):
            return False
        return rest_of_key in target

    def flatten(self):
        def recurse_flatten(prefix, dot_dict):
            for key, value in dot_dict.iteritems():
                new_key = prefix + '.' + key if len(prefix) > 0 else key
                if isinstance(value, DotDict):
                    recurse_flatten(new_key, value)
                else:
                    new_dict[new_key] = value

        new_dict = dict()
        recurse_flatten('', self)
        return new_dict

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]

    __setattr__ = __setitem__
    __getattr__ = __getitem__


@dict_or_raise
def setdefault(source, key, default):
    source[key] = source.get(key, None) or default


@dict_or_raise
def setifnotnone(source, key, value):
    if value is not None:
        source[key] = value
