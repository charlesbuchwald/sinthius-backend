#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 23:31
#

import threading


class ContextLocalManager(threading.local):
    def __init__(self, *args, **kwargs):
        super(ContextLocalManager, self).__init__()
        self.current = dict()


class ContextLocal(object):
    """
    Example:
    --------
    .. code-block:: python
        from bs_core.op.context import ContextLocal
        from tornado.stack_context import StackContext


        class MyContext(ContextLocal):
            def __init__(self, arg1, arg2, *args, **kwargs):
                super(MyContext, self).__init__()
                self.arg1 = arg1
                self.arg2 = arg2


        with StackContext(MyContext(1, [2, 3, 4])):
            assert MyContext.current().arg1 == 1
            assert MyContext.current().arg2 == [2, 3, 4]
    """
    _contexts = ContextLocalManager()
    _default_instance = None

    def __init__(self):
        self.__previous = []

    @classmethod
    def current(cls):
        current = cls._contexts.current.get(cls.__name__, None)
        return current if current is not None else cls._default_instance

    def __enter__(self):
        cls = type(self)
        self.__previous.append(cls._contexts.current.get(cls.__name__, None))
        cls._contexts.current[cls.__name__] = self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        cls = type(self)
        cls._contexts.current[cls.__name__] = self.__previous.pop()

    def __call__(self):
        return self
