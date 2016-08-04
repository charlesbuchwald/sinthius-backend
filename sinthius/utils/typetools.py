#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:28
# ~

from sinthius import compat
from sinthius.utils.decorators import value_or_none


@value_or_none
def to_string(value):
    if isinstance(value, float):
        value = repr(value)
    return compat.binary_type(value)


@value_or_none
def to_number(value):
    try:
        value = int(value)
    except:
        value = float(value)
    return value


@value_or_none
def to_boolean(value):
    value = to_string(value).lower()
    if value in compat.true_values:
        return True
    elif value in compat.false_values:
        return False
    raise TypeError('Expected for true%s or false%s'
                    % (compat.true_values, compat.false_values))


def is_primitive(value):
    return isinstance(value, compat.primitive_type)
