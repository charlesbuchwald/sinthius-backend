#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 09/Jul/2016 00:13
# ~

import collections
from sinthius.conf import settings as global_settings
from sinthius.web.base import BaseHandler
from sinthius_octopus.backend.base import WebSocketHandler, WebSocketApiHandler
from tornado import gen

handlers_list = []
_status = dict()
_clients = collections.defaultdict(set)


class MissionControlHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.render()


class MissionControlAPIHandler(WebSocketApiHandler):
    def get(self, *args, **kwargs):
        self.success('ok')


class MissionControlObserverHandler(WebSocketHandler):
    def open(self, *args, **kwargs):
        if self not in _clients:
            _clients.add(self)

    def on_close(self):
        if self in _clients:
            _clients.remove(self)

    @gen.coroutine
    def on_message(self, message):
        pass

    def __del__(self):
        try:
            _clients.remove(self)
        except:
            pass


if global_settings.MASTER is True:
    handlers_list.extend([
        (r'/a/mc/?', MissionControlHandler),
        (r'/a/mc/api/?', MissionControlAPIHandler),
        (r'/a/mc/observer/?', MissionControlObserverHandler)
    ])


if global_settings.DEBUG is True:
    class ConsoleHandler(BaseHandler):
        def get(self, *args, **kwargs):
            self.render()
    handlers_list.append((r'/a/console/?', ConsoleHandler))
