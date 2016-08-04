#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 13/jun/2016 09:26
# ~

from copy import deepcopy
from functools import wraps
from importlib import import_module
from tornado import gen, httpclient
from sinthius import constants, compat
from sinthius.errors import ClientError
from sinthius.op.manager import purge_settings, factory
from sinthius.utils.async import dispatch, dispatch_return
from sinthius.utils.binary import want_bytes
from sinthius.utils.serializers import parser_types, complex_types, \
    deserialize_complex_types, serialize_complex_types, jsonloads
from sinthius.utils.typetools import to_boolean


def is_read_only(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        _is_read_only(self)
        return dispatch(method(self, *args, **kwargs), **kwargs)
    return wrapper


def _is_read_only(reference):
    method = getattr(reference, 'read_only', None)
    if method is None:
        raise ClientError('Read only attribute is not defined')
    if method is False:
        raise ClientError('Client can to read only')


def _make_adapter(adapter, settings, attributes=None):
    settings = purge_settings(settings, attributes)
    return factory(module=adapter, settings=settings)


def _make_serializer(serializer):
    try:
        module = import_module(serializer)
    except ImportError, e:
        raise ImportError('ImportError("%s"): %s.' % (serializer, e.args[0]))
    methods = [hasattr(module, method) for method in ('dumps', 'loads')]
    if not methods or not all(methods):
        raise ClientError('Serializer "%s" does not define a "dumps/loads" '
                          'attribute' % serializer)
    return module


def _exec_dumps(serializer, module, value, **kwargs):
    if serializer in constants.JSON_SERIALIZER \
            and not compat.ujson_available:
        kwargs.setdefault('default', complex_types)
    else:
        value = serialize_complex_types(value)
    return module.dumps(value, **kwargs)


def _exec_loads(serializer, module, value, **kwargs):
    try:
        if serializer in constants.JSON_SERIALIZER \
                and not compat.ujson_available:
            kwargs.setdefault('object_hook', parser_types)
        value = module.loads(want_bytes(value), **kwargs)
        if serializer not in constants.JSON_SERIALIZER \
                or compat.ujson_available:
            value = deserialize_complex_types(value)
        return value
    except:
        return None


def _parse_arguments(module, settings, attributes):
    settings = {} if not settings else deepcopy(settings)
    for key, require, default in attributes:
        if key in settings:
            value = settings[key]
            if isinstance(default, bool):
                value = to_boolean(value)
            del settings[key]
        else:
            if require:
                raise ClientError('Argument required: %s' % key)
            value = default
        setattr(module, '_%s' % key, value)
    return settings


def _response_json_sanitizer(response):
    result = None
    if isinstance(response, httpclient.HTTPResponse):
        result = response.body
    elif isinstance(response, httpclient.HTTPError):
        result = response.response.body
    return response if not result else jsonloads(result)


@gen.coroutine
def _fetch(url, method='GET', body=None, headers=None, callback=None, **kwargs):
    sanitizer = kwargs.get('sanitizer')
    request = httpclient.HTTPRequest(url, method)
    request.headers = headers
    request.body = body

    for key, value in kwargs.iteritems():
        setattr(request, key, value)

    response = yield gen.Task(httpclient.AsyncHTTPClient().fetch, request)

    if sanitizer:
        response = sanitizer(response)

    dispatch_return(response, callback=callback)


class Client(object):
    def __init__(self, settings, read_only=False):
        self._settings = settings
        self._read_only = read_only

    @property
    def settings(self):
        return self._settings

    @property
    def read_only(self):
        return self._read_only

    def fetch(self, *args, **kwargs):
        raise NotImplementedError()

    def save(self, *args, **kwargs):
        raise NotImplementedError()

    def force_save(self, *args, **kwargs):
        raise NotImplementedError()

    def delete(self, *args, **kwargs):
        raise NotImplementedError()

    def _make_adapter(self):
        raise NotImplementedError()

    def _make_serializer(self):
        raise NotImplementedError()

    def _loads(self, value):
        raise NotImplementedError()

    def _dumps(self, value):
        raise NotImplementedError()


class SerializerAbstract(Client):
    _serializer = None
    _serializer_module = None

    @property
    def serializer(self):
        if self._serializer_module is None:
            self._make_serializer()
        return self._serializer_module

    def _make_serializer(self):
        self._serializer_module = _make_serializer(self._serializer)

    def _dumps(self, value, **kwargs):
        return _exec_dumps(
            self._serializer, self._serializer_module, value, **kwargs)

    def _loads(self, value, **kwargs):
        return _exec_loads(
            self._serializer, self._serializer_module, value, **kwargs)
