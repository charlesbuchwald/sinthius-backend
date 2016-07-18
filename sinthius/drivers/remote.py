#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 13/jun/2016 09:49
# ~

from sinthius.drivers.base import SerializerAbstract, _parse_arguments, _fetch
from tornado import gen


class APIHTTPClient(SerializerAbstract):
    _url = None
    _method = None

    def __init__(self, url=None, method=None, settings=None, read_only=False):
        settings = _parse_arguments(self, settings, (
            ('url', False, url),
            ('method', False, method or 'GET'),
            ('serializer', False, 'json'),
        ))

        super(APIHTTPClient, self).__init__(settings, read_only)
        self._make_serializer()

    @property
    def url(self):
        return self._url

    @property
    def method(self):
        return self._method

    def _sanitize_headers(self, *args, **kwargs):
        raise NotImplementedError()

    def _sanitize_body(self, *args, **kwargs):
        raise NotImplementedError()

    @gen.coroutine
    def fetch(self, url, method='GET', body=None, headers=None, **kwargs):
        response = yield _fetch(url, method, body, headers, **kwargs)
        raise gen.Return(response)
