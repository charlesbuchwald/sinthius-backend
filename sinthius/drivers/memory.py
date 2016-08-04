#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 13/jun/2016 09:29
# ~

from sinthius.conf import settings as global_settings
from redis.client import Redis as RedisSyncClient
from tornadoredis import Client as RedisAsyncClient


SYNC_ARGUMENTS = (
    'host', 'port', 'db', 'password', 'socket_timeout',
    'socket_connect_timeout', 'socket_keepalive',
    'socket_keepalive_options', 'connection_pool', 'unix_socket_path',
    'encoding', 'encoding_errors', 'charset', 'errors',
    'decode_responses', 'retry_on_timeout', 'ssl', 'ssl_keyfile',
    'ssl_certfile', 'ssl_cert_reqs', 'ssl_ca_certs', 'max_connections'
)


ASYNC_ARGUMENTS = (
    'host', 'port', 'unix_socket_path', 'password', 'selected_db',
    'io_loop', 'connection_pool'
)


def get_connector(async=False):
    try:
        if async or global_settings.KEYVALUES_ASYNC:
            return RedisAsyncClient
    except:
        pass
    return RedisSyncClient


def get_client(config, arguments=None, async=None):
    if async is None:
        async = config.get('async', False)
    client = get_connector(async)
    db_settings = {}
    if arguments is None or not isinstance(arguments, tuple):
        arguments = ()
    extra_arguments = SYNC_ARGUMENTS if not async else ASYNC_ARGUMENTS
    arguments = tuple(set(extra_arguments + arguments))
    for key, value in config.iteritems():
        try:
            if key in arguments:
                db_settings[key] = value
        except:
            pass
    return client(**db_settings)
