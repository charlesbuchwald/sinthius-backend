#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:29
# ~

from sinthius import compat
from sinthius.conf import settings
from sinthius.utils.serializers import jsonloads
from sinthius.web.base import APIHandler
from tornado.websocket import WebSocketHandler


class BaseWebSocketHandler(WebSocketHandler, APIHandler):
    _ARG_DEFAULT = []

    def get_header_argument(self, name, default=_ARG_DEFAULT, strip=True):
        source = self._get_header_arguments()
        return self._get_argument(name, default, source, strip)

    def get_header_arguments(self, name, strip=True):
        assert isinstance(strip, bool)
        source = self._get_header_arguments()
        return self._get_arguments(name, source, strip)

    def _get_header_arguments(self):
        values = {}
        arguments = self.request.headers.get(settings.WS_XHEADER_ARGUMENTS)
        if arguments is not None:
            arguments = jsonloads(arguments)
            for key, value in compat.iteritems(arguments):
                if not isinstance(value, compat.list_type):
                    value = [value]
                values[key] = value
        return arguments
