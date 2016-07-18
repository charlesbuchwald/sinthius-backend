#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:28
# ~

import base64
from sinthius import compat, constants
from sinthius.utils.binary import want_bytes
from sinthius.utils.datetimetools import datetime_parser
from sinthius.utils.decorators import value_or_none, string_or_raise
from sinthius.utils.regex import rx_integer, rx_float, rx_isoformat, \
    rx_isoformat_date, rx_isoformat_time, rx_datetime_marker


@value_or_none
def complex_types(value):
    if isinstance(value, compat.text_type):
        return want_bytes(value)
    elif isinstance(value, compat.primitive_type):
        return value
    elif isinstance(value, compat.datetime_type):
        return value.isoformat()
    return compat.binary_type(value)


@value_or_none
def parser_types(value):
    if isinstance(value, compat.string_type):
        if rx_integer.search(value):
            return int(value)
        elif rx_float.search(value):
            return float(value)
        elif rx_datetime_marker.search(value) \
                or rx_isoformat_date.search(value) \
                or rx_isoformat_time.search(value) \
                or rx_isoformat.search(value):
            return datetime_parser(value)
        elif value.lower() in compat.true_values:
            return True
        elif value.lower() in compat.false_values:
            return False
    elif isinstance(value, compat.list_type):
        for index, item in enumerate(value):
            value[index] = parser_types(item)
    elif isinstance(value, dict):
        for key, item in value.iteritems():
            value[key] = parser_types(item)
    elif not isinstance(value, compat.primitive_type):
        value = want_bytes(value)
    return value


@value_or_none
def serialize_complex_types(value):
    if hasattr(value, 'iteritems') or hasattr(value, 'items'):
        return dict(((k, serialize_complex_types(v))
                     for k, v in value.iteritems()))
    elif hasattr(value, '__iter__') \
            and not isinstance(value, compat.string_type):
        return list((serialize_complex_types(v) for v in value))
    return complex_types(value)


@value_or_none
def deserialize_complex_types(value):
    if hasattr(value, 'iteritems') or hasattr(value, 'items'):
        return dict(((k, deserialize_complex_types(v))
                     for k, v in value.iteritems()))
    elif hasattr(value, '__iter__') \
            and not isinstance(value, compat.string_type):
        return list((deserialize_complex_types(v) for v in value))
    return parser_types(value)


def jsondumps(value, encoding=constants.ENCODING, **kwargs):
    if not compat.ujson_available:
        kwargs.setdefault('default', complex_types)
    return compat.json.dumps(value, **kwargs).encode(encoding)


def jsonloads(value, encoding=constants.ENCODING, dquote=True, **kwargs):
    if dquote is True:
        value = value.replace('\'', '"')
    if not compat.ujson_available:
        kwargs.setdefault('object_hook', parser_types)
    return compat.json.loads(value.decode(encoding), **kwargs)


class JSONSerializer(object):
    def loads(self, value, encoding=constants.LATIN1):
        return jsonloads(value, encoding)

    def dumps(self, value, encoding=constants.LATIN1):
        return jsondumps(value, encoding, separators=(',', ':'))


@string_or_raise
def base64_loads(value):
    value = want_bytes(value, constants.ASCII, 'ignore')
    return base64.urlsafe_b64decode(value + b'=' * (-len(value) % 4))


@string_or_raise
def base64_dumps(value):
    value = want_bytes(value)
    return base64.urlsafe_b64encode(value).strip(b'=')


class Base64Serializer(object):
    def loads(self, value):
        return base64_loads(value)

    def dumps(self, value):
        return base64_dumps(value)
