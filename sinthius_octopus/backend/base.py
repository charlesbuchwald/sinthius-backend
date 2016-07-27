#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 13/Jun/2016 20:33
# ~

"""

TODO(berna): varios...
======================

    1. Implementar un esquema de semáforos para el apagado del server.-

    2. Implementar un esquema de colas para la gestión de tareas.-

       2.1. Se podría implmentar AMQP (RabbitMQ or ZMQ).-

    3. Mejorar el driver para redis (reescribirlo) o reemplazar el manejo del
       pub/sub vía ZMQ.-

       3.1. Contemplar la opcion de utilizar MQTT, sería una alternativa
       altamente recomendable.-

    4. Mejorar el manejo de errores.-

"""

import re
import socket
import hashlib
import logging
import collections
from copy import deepcopy
from sinthius.conf import settings as global_settings
from sinthius.drivers import memory, document, database
from sinthius.drivers.base import _fetch
from sinthius.socket.base import BaseWebSocketHandler
from sinthius.utils.async import dispatch
from sinthius.utils.serializers import jsondumps, jsonloads
from sinthius.web.base import APIHandler, ConnectorsMixin, PingHandler
from sinthius.web.application import ServerApplication
from sinthius_octopus.backend.scheme import api_reset
from functools import partial
from datetime import timedelta
from tornado import gen, web, ioloop, httpclient
from tornadoredis import ConnectionError

_RESOURCES = {}
_CHANNEL = 'mission_control'
_CLIENTS = None
_NODE = 'node:{ip}:{port}'
_NODES = None
_FALLEN_NODES = None
_PUBLISHER = None
_MISSION_CONTROL = None
_PULL = None
_PULL_COUNTER = None
API, API_METHODS = api_reset()

rx_node = re.compile(r'^node:(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                     r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):[0-9]{4}$')


def get_local_ip():
    return socket.gethostbyname(socket.gethostname())


class SocketApplication(ServerApplication):
    def __init__(self, **settings):
        super(SocketApplication, self).__init__(**settings)

    # Services (db)

    @property
    def resources(self):
        return _RESOURCES

    # Sockets

    @property
    def clients(self):
        global _CLIENTS
        if _CLIENTS is None:
            _CLIENTS = collections.defaultdict(set)
        return _CLIENTS

    @property
    def nodes(self):
        global _NODES
        if _NODES is None:
            _NODES = {}
        return _NODES

    @property
    def fallen_nodes(self):
        global _FALLEN_NODES
        if _FALLEN_NODES is None:
            _FALLEN_NODES = set()
        return _FALLEN_NODES

    # Mission Control

    @property
    def publisher(self):
        return _PUBLISHER

    @property
    def mission_control(self):
        return _MISSION_CONTROL

    @property
    def pull(self):
        return _PULL

    # Node Information

    _node_id = None
    _node_info = None
    _node_hash = None
    _node_lock = False

    @property
    def node_id(self):
        if self._node_id is None:
            self._node_id = _NODE.format(**self.n_canonical())
        return self._node_id

    @property
    def node_hash(self):
        if self._node_hash is None:
            self._node_hash = self.n_hash()
        return self._node_hash

    @property
    def node_info(self):
        if self._node_info is None:
            self._node_info = {
                'ip': self.n_ip(),
                'port': self.n_port(),
                'hash': self.n_hash(),
                'mode': self.n_mode(),
                'name': self.n_name()
            }
        self._node_info['lock'] = self._node_lock
        self._node_info['update'] = None
        return self._node_info

    # Node

    def n_ip(self):
        return self.settings['nuc_ip'] or get_local_ip()

    def n_port(self):
        return self.settings['nuc_port'] or self.settings['port']

    def n_url(self):
        return '{}:{}'.format(self.n_ip(), self.n_port())

    def n_canonical(self):
        return dict(ip=self.n_ip(), port=self.n_port())

    def n_hash(self):
        h = hashlib.sha256()
        h.update(_NODE.format(**self.n_canonical()))
        return h.hexdigest()

    def n_name(self):
        return self.settings['nuc_name']

    def n_mode(self):
        return self.settings['nuc_mode']

    def n_alive(self):
        return list(set(_NODES.keys()) ^ _FALLEN_NODES)

    def n_fallen(self):
        return list(_FALLEN_NODES)

    #  Lock

    def is_locked(self):
        return self._node_lock

    @gen.coroutine
    def lock(self, **kwargs):
        response = yield self._resume_lock(True)
        raise gen.Return(response)

    @gen.coroutine
    def unlock(self, **kwargs):
        response = yield self._resume_lock(False)
        raise gen.Return(response)

    @gen.coroutine
    def _resume_lock(self, value=None, **kwargs):
        if value is None:
            value = not self._node_lock
        self._node_lock = value
        yield self.register()
        response = yield self.commit('LOCK' if value is True else 'UNLOCK')
        raise gen.Return(response)

    # Publish

    @gen.coroutine
    def commit(self, action='NONE', **kwargs):
        data = dict(action=action)
        if not action.startswith('SYS_'):
            data['node_id'] = self.node_id
            data['node'] = self.node_info
        data.update(kwargs)
        if 'callback' in data:
            del data['callback']
        data = jsondumps(data)
        logging.debug(' * Commit(%s):  %s | %s', _CHANNEL, action, data)
        response = yield gen.Task(self.publisher.publish, _CHANNEL, data)
        raise gen.Return(response)

    @gen.coroutine
    def register(self, **kwargs):
        response = yield gen \
            .Task(self.publisher.set, self.node_id, jsondumps(self.node_info))
        logging.info(' # Register: %s', response)
        raise gen.Return(response)

    @gen.coroutine
    def unregister(self, **kwargs):
        response = yield gen \
            .Task(self.publisher.delete, self.node_id)
        logging.info(' # Unregister: %s', response)
        raise gen.Return(response)

    # Clients

    @gen.coroutine
    def _release_clients(self, **kwargs):
        global _CLIENTS
        logging.debug(' * Closing all clients...')
        for client in self.clients:
            if hasattr(client, 'ws_connection'):
                try:
                    client.close()
                except:
                    pass
            self.clients.remove(client)
        _CLIENTS = None

    # Mission Control

    _mission_control_config = None

    @property
    def mission_control_config(self):
        if self._mission_control_config is None:
            try:
                config = self.settings['keyvalues'][_CHANNEL]['config']
            except:
                config = {
                    'host': '127.0.0.1',
                    'port': 6379,
                    'selected_db': 0,
                    'autoconnect': True
                }
            self._mission_control_config = config
        return self._mission_control_config

    @gen.coroutine
    def _connect_publisher(self, **kwargs):
        global _PUBLISHER
        yield self._disconnect_publisher()
        logging.debug(' * Starting publisher...')
        _publisher = memory.get_client(self.mission_control_config, async=True)
        try:
            _publisher.connect()
            _PUBLISHER = _publisher
            response = True
        except Exception, e:
            logging.error(' ! Publisher (stopped)', exc_info=e)
            response = False
        raise gen.Return(response)

    @gen.coroutine
    def _disconnect_publisher(self, **kwargs):
        global _PUBLISHER
        try:
            if self.publisher is not None:
                logging.debug(' * Stopping publisher...')
                yield gen.Task(self.publisher.disconnect)
        except Exception, e:
            logging.error(' ! Publisher (not started)', exc_info=e)
        _PUBLISHER = None
        raise gen.Return(True)

    @gen.coroutine
    def _connect_mission_control(self, **kwargs):
        global _MISSION_CONTROL
        yield self._disconnect_mission_control()
        logging.debug(' * Starting mission control...')
        _mission_control = memory\
            .get_client(self.mission_control_config, async=True)
        try:
            _mission_control.connect()
            _MISSION_CONTROL = _mission_control
            response = yield self._subscribe_mission_control()
        except Exception, e:
            logging.error(' ! Mission control (stopped)', exc_info=e)
            response = False
        raise gen.Return(response)

    @gen.coroutine
    def _disconnect_mission_control(self, **kwargs):
        global _MISSION_CONTROL
        try:
            if self.mission_control is not None:
                logging.debug(' * Stopping mission control...')
                if _CHANNEL in self.mission_control.subscribed:
                    yield gen.Task(self.mission_control.unsubscribe, _CHANNEL)
                yield gen.Task(self.mission_control.disconnect)
                yield self.unregister()
                yield self.commit('UNSUBSCRIBE')
        except Exception, e:
            logging.error(' ! Mission control (not started)', exc_info=e)
        _MISSION_CONTROL = None
        raise gen.Return(True)

    @gen.coroutine
    def _subscribe_mission_control(self, **kwargs):
        logging.debug(' * Subscribe mission control channel...')
        try:
            yield gen.Task(self.mission_control.subscribe, _CHANNEL)
            self.mission_control.listen(self._on_subscribe)
            response = True
        except Exception, e:
            logging.error(' ! Mission control channel (stopped)', exc_info=e)
            response = False
        raise gen.Return(response)

    @gen.coroutine
    def _on_subscribe(self, message):
        if message.kind == 'message':
            _body, body = strucloads(message.body)
            if body.action.startswith('SYS_'):
                self._stop_pull()
                if body.action == 'SYS_UPDATE':
                    pass
                elif body.action == 'SYS_UPGRADE':
                    pass
                logging.warn(' >> (%s)', body.action)
            elif body.node_id != self.node_id:
                if body.action == 'SUBSCRIBE':
                    value = yield gen.Task(self.publisher.get, body.node_id)
                    self.nodes[body.node_id] = jsonloads(value)
                elif body.action == 'UNSUBSCRIBE' \
                        and body.node_id in self.nodes:
                    del self.nodes[body.node_id]
                logging.warn(' > (%s) %s', body.action, body.node_id)
            self._resume_pull()
        raise gen.Return(True)

    def _connect_pull(self, force=False):
        global _PULL, _PULL_COUNTER
        self._disconnect_pull()
        logging.debug(' * Starting pull...')
        if force is True:
            self._on_pull()
        _PULL = ioloop\
            .PeriodicCallback(self._on_pull, self.settings['pull_delay'] * 1000)
        _PULL_COUNTER = 0

    def _disconnect_pull(self):
        global _PULL, _PULL_COUNTER
        if self.pull is not None:
            logging.debug(' * Stopping pull...')
            self.pull.stop()
        _PULL = None
        _PULL_COUNTER = None

    def _start_pull(self, force=False):
        if self.pull is not None:
            if not self.pull.is_running() or force is True:
                self.pull.start()
                logging.debug(' * Pull task started')

    def _stop_pull(self, force=False):
        if self.pull is not None:
            if self.pull.is_running() or force is True:
                self.pull.stop()
                logging.debug(' * Pull task stopped')

    def _resume_pull(self):
        nodes = len(self.nodes)
        if nodes > 0:
            self._start_pull()
        else:
            self._stop_pull()

    @gen.coroutine
    def _on_pull(self, **kwargs):
        global _PULL_COUNTER
        self._stop_pull()
        if self._SHUTTING_DOWN is False:
            check_times = self.settings['pull_check_times']
            if _PULL_COUNTER is None or _PULL_COUNTER >= check_times:
                try:
                    response = yield self._fetch_pull()
                except:
                    response = False
                if not response:
                    if response is False:
                        logging.error(' ! Connection refused')
                        if self._RECONNECTING is None:
                            yield self._on_try_reconnect()
                    else:
                        logging.warn(' > Node removed by administrator')
                        self.shutdown(True)
                    raise gen.Return(response)
                _PULL_COUNTER = 0
                logging.debug(' * Check reset')
            for node, value in self.nodes.iteritems():
                value = Struct(value)
                url = 'http://{ip}:{port}/ping'\
                    .format(ip=value.ip, port=value.port)
                response = yield _fetch(url)
                if isinstance(response, httpclient.HTTPResponse):
                    if response.code != 200:
                        logging\
                            .error(' ! Fetch ~ %s :: %s', node, response.reason)
                        if node not in self.fallen_nodes:
                            self.fallen_nodes.add(node)
                    else:
                        logging\
                            .debug(' * Fetch ~ %s :: %s', node, response.body)
                        if node in self.fallen_nodes:
                            self.fallen_nodes.remove(node)
                elif isinstance(response, httpclient.HTTPError):
                    logging\
                        .error(' [!] Fetch ~ %s :: %s', node, response.message)
                else:
                    logging\
                        .error(' [!!] Fetch ~ %s :: %s', node, type(response))
            _PULL_COUNTER += 1
            check = len(self.nodes)
            fallen = len(self.fallen_nodes)
            logging.debug(' * Check ~ %s of %s nodes', check - fallen, check)
            logging.debug(' * Fallen ~ %s of %s nodes', fallen, check)
            logging.debug(' * Pull ~ %s of %s to reset', _PULL_COUNTER,
                          check_times)
            self._resume_pull()
        raise gen.Return(True)

    @gen.coroutine
    def _fetch_pull(self, **kwargs):
        global _NODES, _FALLEN_NODES
        if self._SHUTTING_DOWN is False:
            logging.debug(' * Recovering nodes...')
            _NODES = {}
            _FALLEN_NODES = set()
            response = yield gen.Task(self.publisher.keys, 'node:*')
            if self.node_id not in response:
                logging.error(' ! Node not registered: %s', self.node_id)
                raise gen.Return(None)
            logging.debug(' * Recovered nodes:')
            for node in response:
                value = yield gen.Task(self.publisher.get, node)
                _data, data = strucloads(value)
                node_id = _NODE.format(ip=data.ip, port=data.port)
                if node_id != self.node_id:
                    self.nodes[node_id] = _data
            logging.debug(' : Not found' if not self.nodes
                          else jsondumps(self.nodes, indent=2))
        raise gen.Return(True)

    @gen.coroutine
    def remove_fallen_nodes(self, **kwargs):
        global _FALLEN_NODES
        nodes = list(self.fallen_nodes)
        if self._SHUTTING_DOWN is False:
            for node in self.fallen_nodes:
                yield gen.Task(self.publisher.delete, node)
            self.fallen_nodes.clear()
        raise gen.Return(nodes)

    # Connection

    @gen.coroutine
    def reconnect(self, subscribe=True, **kwargs):
        response = yield self._connect_publisher()
        if response is True:
            response = yield self.register()
            if response is True:
                yield self._fetch_pull()
                response = yield self._connect_mission_control()
                if response is True and subscribe is True:
                    yield self.commit('SUBSCRIBE')
        raise gen.Return(response)

    _RECONNECTING = None

    @gen.coroutine
    def _on_try_reconnect(self, **kwargs):
        loop = ioloop.IOLoop.current()
        logging.warn(' > Trying reconnect...')
        try:
            if self._RECONNECTING is not None:
                loop.remove_timeout(self._RECONNECTING)
            self.publisher.connect()
            self.mission_control.connect()
            logging.info(' + Reconnected')
            yield self._subscribe_mission_control()
            self._RECONNECTING = None
            yield self._on_pull()
        except ConnectionError, e:
            logging.error(' ! Try reconnect (error): %s', e.message)
            deadline = \
                timedelta(seconds=self.settings['pull_reconnect_delay'])
            self._RECONNECTING = \
                loop.add_timeout(deadline, self._on_try_reconnect)
        except Exception, e:
            logging.error(' ! Try reconnect (critical)...', exc_info=e)
            exit()
        raise gen.Return()

    def _release_try_reconnect(self):
        try:
            if self._RECONNECTING is not None:
                ioloop.IOLoop.current().remove_timeout(self._RECONNECTING)
        except Exception, e:
            logging.error(' ! Release try reconnect (error)', exc_info=e)
        self._RECONNECTING = None

    # Control

    _STARTING = None

    @gen.coroutine
    def start(self, **kwargs):
        loop = ioloop.IOLoop.current()
        try:
            if self._STARTING is not None:
                logging.warn(' > Trying start...')
                loop.remove_timeout(self._STARTING)
            response = yield self.reconnect()
            if response is True:
                self._connect_pull(True)
            else:
                raise RuntimeError, response
            self._STARTING = None
        except Exception, e:
            force = kwargs.get('force', self.settings.get('force_start', False))
            if force is True and self._SHUTTING_DOWN is False:
                self._STARTING = loop.add_timeout(
                    timedelta(seconds=2), partial(self.start, **kwargs))
            else:
                raise e
        raise gen.Return(None)

    _SHUTTING_DOWN = False

    @gen.coroutine
    def shutdown(self, force=False, exit_callback=None, **kwargs):
        self._SHUTTING_DOWN = True
        self._disconnect_pull()
        self._release_try_reconnect()
        self._release_clients()
        yield self._disconnect_mission_control()
        yield self._disconnect_publisher()
        self._SHUTTING_DOWN = False
        if force is True:
            if callable(exit_callback):
                exit_callback()
            else:
                self.exit_callback()
        raise gen.Return(True)

    def health(self):
        response = {}
        try:
            _publisher = self.publisher.connection.connected()
        except:
            _publisher = False
        response['publisher'] = _publisher
        try:
            _mission_control = self.mission_control.connection.connected()
        except:
            _mission_control = False
        response['mission_control'] = _mission_control
        response['mission_control_channel'] = \
            bool(_CHANNEL in self.mission_control.subscribed)
        result = all(response.values())
        logging.info(' # HEALTH PING (%s): %s', result, response)
        response['scope'] = \
            {'nodes': {'alive': list(set(_NODES.keys()) ^ _FALLEN_NODES),
                       'fallen': list(_FALLEN_NODES)}}
        response.update(self.uptime())
        return result, {'status': result, 'details': response}

    def frontend_repository(self):
        path = str(self.settings['frontend_path'])
        return path.format(**self.settings.get('paths', {}))


class Struct(object):
    def __init__(self, values):
        for key, value in values.iteritems():
            if isinstance(value, dict):
                setattr(self, key, Struct(value))
            else:
                setattr(self, key, value)

    def __getitem__(self, val):
        return self.__dict__[val]

    def __repr__(self):
        return '{%s}' % str(
            ', '.join('%s : %s' % (k, repr(v))
            for (k, v) in self.__dict__.iteritems())
        )


def strucloads(value):
    value = jsonloads(value)
    return value, Struct(value)


class ObjectStorage(dict):
    _expires = dict()

    def __init__(self, data=None, **kwargs):
        super(ObjectStorage, self).__init__()
        if isinstance(data, dict):
            self.update(data)
        self.update(kwargs)

    def get(self, key, **kwargs):
        response = super(ObjectStorage, self).get(key, None)
        return dispatch(response, **kwargs)

    def set(self, key, value, expire=None, pexpire=None,
            only_if_not_exists=False, only_if_exists=False, **kwargs):
        response = None
        if (key not in self and only_if_not_exists is True) \
                or (key in self and only_if_exists is True):
            self[key] = value
            self._expires[key] = expire or pexpire
        return dispatch(response, **kwargs)

    def append(self, key, value, **kwargs):
        self[key] = value
        return dispatch(self[key], **kwargs)

    def delete(self, key, **kwargs):
        response = self[key]
        try:
            del self[key]
        except:
            pass
        return dispatch(response, **kwargs)


class ResourceMixin(ConnectorsMixin):
    def _find_resource(self, key, name):
        try:
            value = getattr(self, 'settings', {})[key][name]
            return deepcopy(value)
        except:
            return None

    def _add_resource(self, key, name, client):
        resource = '%s_%s' % (key, name)
        if resource not in _RESOURCES:
            config = self._find_resource(key, name)
            if config is not None:
                try:
                    conn = client(config['config'], async=True)
                    if conn:
                        _RESOURCES[resource] = conn
                except Exception, e:
                    raise RuntimeError, e.__str__()
            else:
                raise ValueError, 'Resource not supported'
        return _RESOURCES[resource]

    def db_connector(self, name):
        return self._add_resource('databases', name, database.get_client)

    def kv_connector(self, name):
        return self._add_resource('keyvalues', name, memory.get_client)

    def ob_connector(self, name):
        return self._add_resource('objects', name, document.get_client)

    @gen.coroutine
    def get_objects(self, **kwargs):
        response = yield gen.Task(self.object.fetch, **kwargs)
        raise gen.Return(ObjectStorage(response))



class WebSocketHandler(ResourceMixin, BaseWebSocketHandler):
    @property
    def clients(self):
        return self.application.clients

    @gen.coroutine
    def on_message(self, message):
        action = str(message).upper()
        if action in API_METHODS:
            api = API[action]
            try:
                getattr(self, api.function, None)(api, message)
            except:
                mse = 'Method "%s" not defined.' % action
                self.write_message(self.json_normalizer(1001, mse))
        else:
            mse = 'Method "%s" not supported.' % action
            self.write_message(self.json_normalizer(1000, mse))


class WebSocketApiHandler(ResourceMixin, APIHandler):
    def get_record(self, arguments):
        if hasattr(arguments, 'arguments'):
            arguments = arguments.arguments
        record = {}
        errors = []
        for argument in arguments:
            error = None
            value = self.get_argument(argument.name, None, True)
            if argument.required:
                if value is None:
                    error = '%s, is required.'
                elif issubclass(argument.type, list):
                    try:
                        value = value.split(',')
                    except:
                        error = '%s, bad format.'
                else:
                    try:
                        value = argument.type(value)
                    except Exception, e:
                        error = '%s, ' + e.__str__()
            if error is None:
                record[argument.name] = value
            else:
                errors.append(error % argument.name)
        return record, errors

    def success(self, response, code=None, message=None, **kwargs):
        self.normalize_response(code, message, response, **kwargs)

    def error(self, message, code=None, response=None, **kwargs):
        self.normalize_response(code, message, response, **kwargs)


class StatsHandler(APIHandler):
    def get(self, *args, **kwargs):
        result, response = self.application.health()
        if result is True:
            chunk = self.application.stats()
            chunk['health'] = response
        self.normalize_response(response=chunk, sort_keys=True)


handlers_list = [
    (r'/stats', StatsHandler),
    (r'/ping', PingHandler),
]


if global_settings.DEBUG is True:
    class HomeHandler(APIHandler):
        def get(self, *args, **kwargs):
            self.render()
    handlers_list.append((r'/', HomeHandler))

else:
    handlers_list.append((r'/', web.RedirectHandler, {'url': '/stats'}))
