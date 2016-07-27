#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 09/Jul/2016 00:13
# ~

import git
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


class MissionControlAPIGitHandler(WebSocketApiHandler):
    def get(self, action, *args, **kwargs):
        message = None
        PATH = self.application.frontend_repository()
        repo = git.Repo(PATH)
        if action == 'status':
            message = repo.git.status('-s').split('\n')
        elif action == 'fetch':
            try:
                message = repo.git.fetch()
            except Exception, e:
                message = e.__str__()
        elif action == 'pull':
            try:
                repo.git.fetch()
                message = repo.git.pull()
            except Exception, e:
                message = e.__str__()
        elif action == 'update':
            try:
                import subprocess
                subprocess\
                    .call(['git', 'add', '.'], cwd=PATH)
                subprocess\
                    .call(['git', 'commit', '-m', 'LOCAL UPDATE'], cwd=PATH)
                message = 'Success'
            except Exception, e:
                message = e.__str__()
        self.success({'action': action, 'message': message})


class MissionControlAPIUpdateHandler(WebSocketApiHandler):
    def get(self, action, *args, **kwargs):
        self.application.commit('sys_{}'.format(action).upper())


class MissionControlAPIRemoveFallenHandler(WebSocketApiHandler):
    @gen.coroutine
    def get(self, *args, **kwargs):
        response = yield self.application.remove_fallen_nodes()
        self.success(response)


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
        (r'/a/mc/api/git/(fetch|pull|update|status)/?',
         MissionControlAPIGitHandler),
        (r'/a/mc/api/(update|upgrade)/?', MissionControlAPIUpdateHandler),
        (r'/a/mc/api/remove/fallen/?', MissionControlAPIRemoveFallenHandler),
        (r'/a/mc/observer/?', MissionControlObserverHandler)
    ])


if global_settings.DEBUG is True:
    class ConsoleHandler(BaseHandler):
        def get(self, *args, **kwargs):
            self.render()
    handlers_list.append((r'/a/console/?', ConsoleHandler))
