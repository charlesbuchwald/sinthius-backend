#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:28
# ~

from itertools import izip
from sinthius import constants, compat
from sinthius.utils.binary import want_bytes
from sinthius.utils.decorators import value_or_none, value_or_raise
from sinthius.utils.regex import rx_camel_case_split


try:
    from hmac import compare_digest
    safecompare = compare_digest

except:
    def safecompare(one, two):
        one = want_bytes(one)
        two = want_bytes(two)
        if len(one) != len(two):
            return False
        rv = 0
        for x, y in izip(one, two):
            rv |= ord(x) ^ ord(y)
        return rv == 0


@value_or_none
def camel_case_split(value, separator='-'):
    value = rx_camel_case_split\
        .sub(r'{separator}\1'.format(separator=separator), value)
    return value, value.lower(), value.upper()


@value_or_raise
def pluralize(count, singular='', plural='s'):
    return singular if count == 1 else plural


@value_or_none
def force_text(value, encoding=constants.ENCODING, strings_only=False,
               errors='strict'):
    if isinstance(value, compat.text_type):
        return value
    try:
        if not isinstance(value, compat.string_type):
            if hasattr(value, '__unicode__'):
                value = compat.text_type(value)
            else:
                value = compat.text_type(bytes(value), encoding, errors)
        else:
            value = value.decode(encoding, errors)
    except UnicodeDecodeError as e:
        if not isinstance(value, Exception):
            raise UnicodeError(value, *e.args)
        else:
            value = ' '.join(force_text(arg, encoding, strings_only, errors)
                             for arg in value)
    return value
