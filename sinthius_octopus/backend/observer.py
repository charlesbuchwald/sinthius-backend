#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 26/Jun/2016 20:07
# ~

import logging
from sinthius.drivers.base import _fetch
from sinthius_octopus.backend.base import WebSocketApiHandler, \
    WebSocketHandler, rx_node
from tornado import gen, httpclient


def _log_error(cls, e):
    message = e.__str__()
    logging.error(' ! %s - %s', cls.request.path, message)
    cls.error(message)


class GetHandler(WebSocketApiHandler):
    @gen.coroutine
    def get(self, *args, **kwargs):
        try:
            node = self.get_argument('node', '')
            if not rx_node.search(node) or node not in self.application.nodes:
                raise TypeError, 'Node "%s" not supported' % node
            node = self.application.nodes[node]
            url = 'http://{ip}:{port}/api/node/health'.format(**node)
            response = yield _fetch(url)
            if isinstance(response, httpclient.HTTPResponse):
                if response.code == 200:
                    self.string_response(response.body)
                else:
                    raise AssertionError, \
                        '{} : {}'.format(response.reason, response.error)
            else:
                raise AssertionError, response.message
        except Exception, e:
            _log_error(self, e)


class NodeHandler(WebSocketApiHandler):
    def get(self, *args, **kwargs):
        chunk = dict(
            node=self.application.node_id,
            **self.application.node_info)
        self.success(chunk, sort_keys=True)


class NodeHealthHandler(WebSocketApiHandler):
    def get(self, *args, **kwargs):
        chunk = dict(
            node=self.application.node_id,
            health=self.application.health()[1],
            **self.application.node_info)
        self.success(chunk, sort_keys=True)


class NodeHashHandler(WebSocketApiHandler):
    def get(self, *args, **kwargs):
        self.success({'hash': self.application.n_hash()})


class NodeLockHandler(WebSocketApiHandler):
    @gen.coroutine
    def get(self, *args, **kwargs):
        try:
            response = yield self.application.lock()
            self.success({'lock': bool(response)})
        except Exception, e:
            _log_error(self, e)


class NodeUnlockHandler(WebSocketApiHandler):
    @gen.coroutine
    def get(self, *args, **kwargs):
        try:
            response = yield self.application.unlock()
            self.success({'unlock': bool(response)})
        except Exception, e:
            _log_error(self, e)


class NodesHandler(WebSocketApiHandler):
    def get(self, *args, **kwargs):
        alive = self.application.n_alive()
        fallen = self.application.n_fallen()
        self.success({
            'alive': {'nodes': alive, 'total': len(alive)},
            'fallen': {'nodes': fallen, 'total': len(fallen)}
        }, sort_keys=True)


class NodesCacheHandler(WebSocketApiHandler):
    def get(self, *args, **kwargs):
        self.success(self.application.nodes.values())


class NodesAliveHandler(WebSocketApiHandler):
    def get(self, *args, **kwargs):
        alive = self.application.n_alive()
        self.success({
            'alive': {'list': alive, 'total': len(alive)},
        }, sort_keys=True)


class NodesAliveHealthHandler(WebSocketApiHandler):
    @gen.coroutine
    def get(self, *args, **kwargs):
        try:
            nodes = self.application.n_alive()
            alive = []
            for item in sorted(nodes):
                node = self.application.nodes[item]
                url = 'http://{ip}:{port}/api/node/health'.format(**node)
                response = yield _fetch(url)
                if isinstance(response, httpclient.HTTPResponse):
                    if response.code == 200:
                        alive.append(
                            self.json_loads(response.body).get('response'))
            self.success({
                'alive': {'nodes': alive, 'total': len(alive)},
            }, sort_keys=True)
        except Exception, e:
            _log_error(self, e)


class NodesFallenHandler(WebSocketApiHandler):
    def get(self, *args, **kwargs):
        fallen = self.application.n_fallen()
        self.success({
            'fallen': {'nodes': fallen, 'total': len(fallen)}
        }, sort_keys=True)


class NodesHashHandler(WebSocketApiHandler):
    def get(self, *args, **kwargs):
        alive = {k:v['hash'] for k, v in self.application.nodes.iteritems()}
        fallen = {}
        for node in self.application.n_fallen():
            fallen[node] = alive[node]
            del alive[node]
        self.success({
            'alive': {'nodes': alive, 'total': len(alive)},
            'fallen': {'nodes': fallen, 'total': len(fallen)}
        }, sort_keys=True)


class NodesCanonicalHandler(WebSocketApiHandler):
    def get(self, *args, **kwargs):
        alive = {k: {'ip': v['ip'], 'port': v['port']}
                 for k, v in self.application.nodes.iteritems()}
        fallen = {}
        for node in self.application.n_fallen():
            fallen[node] = alive[node]
            del alive[node]
        self.success({
            'alive': {'nodes': alive, 'total': len(alive)},
            'fallen': {'nodes': fallen, 'total': len(fallen)}
        }, sort_keys=True)


# Web Socket

class ObserverHandler(WebSocketHandler):
    def open(self, *args, **kwargs):
        self.application.clients.add(self)

    def on_close(self):
        self.application.clients.remove(self)


# Handlers

handlers_list = [
    (r'/api/get/?', GetHandler),
    (r'/api/node/?', NodeHandler),
    (r'/api/node/hash/?', NodeHashHandler),
    (r'/api/node/health/?', NodeHealthHandler),
    (r'/api/node/lock/?', NodeLockHandler),
    (r'/api/node/unlock/?', NodeUnlockHandler),
    (r'/api/nodes/?', NodesHandler),
    (r'/api/nodes/cache/?', NodesCacheHandler),
    (r'/api/nodes/alive/?', NodesAliveHandler),
    (r'/api/nodes/alive/health/?', NodesAliveHealthHandler),
    (r'/api/nodes/fallen/?', NodesFallenHandler),
    (r'/api/nodes/hash/?', NodesHashHandler),
    (r'/api/nodes/canonical/?', NodesCanonicalHandler),
    (r'/ws/observer/?', ObserverHandler),
]
