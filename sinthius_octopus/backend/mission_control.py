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
from sinthius_octopus.backend.base import WebSocketHandler, \
    WebSocketApiHandler, git_commit, git_fetch, git_pull, git_status, git_log
from tornado import gen

handlers_list = []
# _status = dict()
# _clients = collections.defaultdict(set)


class MissionControlHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.render()


class MissionControlAPIGitHandler(WebSocketApiHandler):
    @gen.coroutine
    def get(self, action, *args, **kwargs):
        message, error = None, None
        _repo = self.application.frontend_repository()
        try:
            if action == 'log':
                git_function = git_log
            elif action == 'fetch':
                git_function = git_fetch
            elif action == 'pull':
                git_function = git_pull
            elif action == 'update':
                git_function = git_commit
            else:
                git_function = git_status
            message, error = yield git_function(_repo)
        except Exception, e:
            message = e.__str__()
        self.success({'action': action, 'message': message, 'error': error})


class MissionControlAPIUpdateHandler(WebSocketApiHandler):
    @gen.coroutine
    def get(self, action, *args, **kwargs):
        response = \
            yield self.application.commit('sys_{}'.format(action).upper())
        self.success(response)


class MissionControlAPIRemoveFallenHandler(WebSocketApiHandler):
    @gen.coroutine
    def get(self, *args, **kwargs):
        response = yield self.application.remove_fallen_nodes()
        self.success(response)


# class MissionControlObserverHandler(WebSocketHandler):
#     def open(self, *args, **kwargs):
#         if self not in _clients:
#             _clients.add(self)
#
#     def on_close(self):
#         if self in _clients:
#             _clients.remove(self)
#
#     @gen.coroutine
#     def on_message(self, message):
#         pass
#
#     def __del__(self):
#         try:
#             _clients.remove(self)
#         except:
#             pass


if global_settings.MASTER is True:
    handlers_list.extend([
        (r'/a/mc/?', MissionControlHandler),
        (r'/a/mc/api/git/(fetch|pull|update|status|log)/?',
         MissionControlAPIGitHandler),
        (r'/a/mc/api/(update|upgrade)/?', MissionControlAPIUpdateHandler),
        (r'/a/mc/api/remove/fallen/?', MissionControlAPIRemoveFallenHandler),
        # (r'/a/mc/observer/?', MissionControlObserverHandler)
    ])


if global_settings.DEBUG is True:
    class ConsoleHandler(BaseHandler):
        def get(self, *args, **kwargs):
            self.render()
    handlers_list.append((r'/a/console/?', ConsoleHandler))
