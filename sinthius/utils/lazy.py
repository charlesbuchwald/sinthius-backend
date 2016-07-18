#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:28
# ~

import copy
import copy_reg
import operator
from sinthius import compat


def new_method_proxy(func):
    def inner(self, *args):
        if self._wrapped is compat.empty:
            self._setup()
        return func(self._wrapped, *args)
    return inner


class LazyObject(object):
    _wrapped = None

    def __init__(self):
        self._wrapped = compat.empty

    __getattr__ = new_method_proxy(getattr)

    def __setattr__(self, name, value):
        if name == '_wrapped':
            self.__dict__['_wrapped'] = value
        else:
            if self._wrapped is compat.empty:
                self._setup()
            setattr(self._wrapped, name, value)

    def __delattr__(self, name):
        if name == '_wrapped':
            raise TypeError("Can't delete _wrapped.")
        if self._wrapped is compat.empty:
            self._setup()
        delattr(self._wrapped, name)

    def _setup(self):
        raise NotImplementedError('Subclasses of LazyObject must provide a '
                                  '_setup() method')

    def __getstate__(self):
        if self._wrapped is compat.empty:
            self._setup()
        return self._wrapped.__dict__

    @classmethod
    def __newobj__(cls, *args):
        return cls.__new__(cls, *args)

    def __reduce_ex__(self, proto):
        if proto >= 2:
            return self.__newobj__, (self.__class__,), \
                   self.__getstate__()
        else:
            return copy_reg._reconstructor, (self.__class__, object, None), \
                   self.__getstate__()

    def __deepcopy__(self, memo):
        if self._wrapped is compat.empty:
            result = type(self)()
            memo[id(self)] = result
            return result
        return copy.deepcopy(self._wrapped, memo)

    if compat.PY2:
        __str__ = new_method_proxy(str)
        __unicode__ = new_method_proxy(unicode)
        __nonzero__ = new_method_proxy(bool)
    else:
        __bytes__ = new_method_proxy(bytes)
        __str__ = new_method_proxy(str)
        __bool__ = new_method_proxy(bool)

    __dir__ = new_method_proxy(dir)
    __class__ = property(new_method_proxy(operator.attrgetter('__class__')))
    __eq__ = new_method_proxy(operator.eq)
    __ne__ = new_method_proxy(operator.ne)
    __hash__ = new_method_proxy(hash)
    __getitem__ = new_method_proxy(operator.getitem)
    __setitem__ = new_method_proxy(operator.setitem)
    __delitem__ = new_method_proxy(operator.delitem)
    __iter__ = new_method_proxy(iter)
    __len__ = new_method_proxy(len)
    __contains__ = new_method_proxy(operator.contains)


_super = super


class SimpleLazyObject(LazyObject):
    def __init__(self, func):
        self.__dict__['_setupfunc'] = func
        _super(SimpleLazyObject, self).__init__()

    def _setup(self):
        self._wrapped = self._setupfunc()

    def __repr__(self):
        if self._wrapped is compat.empty:
            repr_attr = self._setupfunc
        else:
            repr_attr = self._wrapped
        return '<%s: %r>' % (type(self).__name__, repr_attr)

    def __deepcopy__(self, memo):
        if self._wrapped is compat.empty:
            result = SimpleLazyObject(self._setupfunc)
            memo[id(self)] = result
            return result
        return copy.deepcopy(self._wrapped, memo)
