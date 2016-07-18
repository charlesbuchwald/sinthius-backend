#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 13/jun/2016 09:31
# ~
# TODO(berna): I need to update the pymongo driver.-

from sinthius.conf import settings as global_settings
try:
    from motor import MotorClient, MotorReplicaSetClient
except:
    MotorClient, MotorReplicaSetClient = None, None
from pymongo import MongoClient, MongoReplicaSetClient
from pymongo.common import validate

MONGODB_ARGUMENTS = (
    'replicaset', 'w', 'wtimeout', 'wtimeoutms', 'fsync', 'j', 'journal',
    'connecttimeoutms', 'maxpoolsize', 'socketkeepalive', 'sockettimeoutms',
    'waitqueuetimeoutms', 'waitqueuemultiple', 'ssl', 'ssl_keyfile',
    'ssl_certfile', 'ssl_cert_reqs', 'ssl_ca_certs', 'ssl_match_hostname',
    'read_preference', 'readpreference', 'readpreferencetags',
    'localthresholdms', 'serverselectiontimeoutms', 'authmechanism',
    'authsource', 'authmechanismproperties', 'document_class', 'tz_aware',
    'uuidrepresentation', 'connect', 'event_listeners'
)


def get_connector(async=False):
    try:
        if async or global_settings.DATABASES_ASYNC:
            return MotorClient, MotorReplicaSetClient
    except:
        pass
    return MongoClient, MongoReplicaSetClient


def get_client(config, arguments=None, async=None):
    if async is None:
        async = config.get('async', False)
    client, rs_client = get_connector(async)
    db_settings = {}
    if arguments is None or not isinstance(arguments, tuple):
        arguments = ()
    arguments = tuple(set(MONGODB_ARGUMENTS + arguments))
    for key, value in config.iteritems():
        try:
            if key in arguments:
                validate(key, value)
                db_settings[key] = value
        except:
            pass
    if 'replicaset' not in db_settings:
        return client(**db_settings)
    else:
        return rs_client(**db_settings)


def get_database(config, arguments=None):
    client = get_client(config, arguments)
    database = client[config.get('database', 'test')]
    db_auth = [config.get('username', None), config.get('password', None)]
    if all(db_auth):
        database.authenticate(*db_auth)
    return database