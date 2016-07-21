#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 13/jun/2016 13:15
# ~

# Erase for production
DISABLE_BROWSER = True
SHUTDOWN_SECONDS = 0
# ~

# Nuc
MASTER = False
NUC_NAME = 'NUC'
NUC_IP = '127.0.0.1'
NUC_PORT = 4000
NUC_MODE = 0
NUC_DESCRIPTION = 'Nuc description here...'

# Server
PORT = NUC_PORT
FORCE_START = True
APPLICATION = 'sinthius_octopus.backend.base.SocketApplication'
PULL_DELAY = 5  # in seconds
PULL_RECONNECT_DELAY = 2  # in seconds
PULL_CHECK_TIMES = 2
FRONTEND_PATH = '{src}/frontend'

HANDLERS = (
    'sinthius_octopus.backend.mission_control',
    'sinthius_octopus.backend.observer',
    'sinthius_octopus.backend.base',
)

DATABASES = {
    'default': {
        'name': 'sinthius',
        'config': {
            'host': 'localhost',
            'port': 27017
        }
    }
}

KEYVALUES = {
    'default': {
        'name': 'sinthius',
        'config': {
            'host': 'localhost',
            'port': 6379,
            'selected_db': 1
        }
    },
    'mission_control': {
        'name': 'mission_control',
        'config': {
            'host': 'localhost',
            'port': 6379,
            'selected_db': 0,
            'autoconnect': True
        }
    }
}

OBJECTS = {
    'default': {
        'name': 'sinthius',
        'config': {
            'filename': 'sinthius.file',
            'settings': {
                'root': '{object}',
                'makefile': True,
                'serializer': 'msgpack'
            }
        }
    }
}
