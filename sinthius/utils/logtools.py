#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:28
# ~

import logging
import traceback
from functools import partial
from sinthius.utils.binary import want_bytes
from sinthius.utils.decorators import value_or_none, string_or_none
from sinthius.utils.serializers import jsondumps
from sinthius.utils.terms import colorize


def trace(value=None):
    if value is not None:
        if isinstance(value, (tuple, list, dict, set)):
            value = jsondumps(value)
        logging.error(value)
    logging.error(traceback.format_exc())


def printdumps(value):
    print jsondumps(value)


@string_or_none
def printcolorizer(value, **kwargs):
    print colorize(value, **kwargs)


def debugdumps(value):
    logging.debug(jsondumps(value))


@string_or_none
def debugcolorizer(value, **kwargs):
    logging.debug(colorize(value, **kwargs))


@value_or_none
def format_log_argument(value):
    value = want_bytes(value)
    max_len = 256
    if len(value) <= max_len:
        return value
    return '%s...[%d bytes truncated]' % (value[:max_len], len(value) - max_len)


def format_arguments(*args, **kwargs):
    def _format_arg(arg):
        return format_log_argument(arg)

    args = [_format_arg(arg) for arg in args]
    kwargs = {key: _format_arg(value) for key, value in kwargs.iteritems()}
    return "(args=%s, kwargs=%s)" % (args, kwargs)


def format_function_call(func, *args, **kwargs):
    while type(func) is partial:
        args = func.args + args
        if func.keywords:
            kwargs.update(func.keywords)
        func = func.func
    return "%s%s" % (func.__name__, format_arguments(*args, **kwargs))
