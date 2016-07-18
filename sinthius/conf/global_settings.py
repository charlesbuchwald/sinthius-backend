#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:29
# ~

from __future__ import unicode_literals


# SERVER
# ~~~~~~

DEBUG = False
TRACK = False
SSL = False
API = False
XHEADERS = False
XSRF_COOKIES = False
XSRF_COOKIES_VERSION = 1
WS_XHEADER_ARGUMENTS = 'X-Arguments'
COOKIE_SECRET = None
COMPRESS_RESPONSE = True
AUTORELOAD = False
PREFORK_PROCESS = -1
ASYNC_WORKERS = 8
ASYNC_HTTP_CLIENT = 'tornado.curl_httpclient.CurlAsyncHTTPClient'
SHUTDOWN_SECONDS = 10
LOG_MAX_BUFFER = 1 << 20
LOG_FLUSH_INTERVAL = 60 * 60
LOG_ERROR_FLUSH_INTERVAL = 2 * 60
MAIN = 'sinthius.server.main'
APPLICATION = 'sinthius.web.application.ServerApplication'
DISABLE_BROWSER = False
PING_RESPONSE = 'hello kitty, =^.^='


# DOMAINS
# ~~~~~~~

# Default
IP = '127.0.0.1'
DOMAIN = 'localhost'
PORT = 8000

# Allowed
DOMAINS = {
    'local': {
        'ip': '127.0.0.1',
        'domain': 'localhost',
        'port': 8000
    },
    'remote': {
        'ip': '127.0.0.1',
        'domain': 'remote.local',
        'port': 8000
    },
    'short': {
        'ip': '127.0.0.1',
        'domain': 'short.local',
        'port': 8000
    }
}


# PATHS
# ~~~~~

# Root '/value'
ROOT_PATH = '../server'


# WEB
# ~~~

# Handler ('module.path', ...)
HANDLERS = ()

# Modules ('module.path', ...)
TRANSFORMS = ()

# Modules (('ModuleName', 'module.path.ClassName'), ...)
UI_MODULES = ()
UI_METHODS = ()

# Account (url)
ROOT_URL = '/'
LOGIN_URL = '/auth/login'
LOGOUT_URL = '/auth/logout'


# SECURITY
# ~~~~~~~~

# Secret Key
SECRET_KEY = None

# Signing Key
SIGNING_KEY = None

# Crypto (RSA)
PASSPHRASE = None
PASSPHRASE_KEY = None
PASSPHRASE_FILE = None
PRIVATE_RSA_FILE = None
PUBLIC_RSA_FILE = None

# Session
SESSION_ID = 'sid'
SESSION_COOKIE_ID = 'sid'
SESSION_HEADER_ID = 'X-Session-ID'
SESSION_DAYS = 30
SESSION_SECONDS = SESSION_DAYS * (60 * 60 * 24)
SESSION_ADAPTER = 'session'
SESSION_SERIALIZER = 'json'
SESSION_SECURE = False


# LOCALE
# ~~~~~~

# Locale (default)
LOCALE = 'en_us'

# Locale Supported (('iso2', 'Name'), ...)
LOCALE_SUPPORTED = (
    ('es_LA', 'Español'),
    ('en_US', 'English')
)


# STORAGES
# ~~~~~~~~

# NoSQL DataBase {'id': {'item': 'value'}}
DATABASES = {}

# Key-Value DataBase {'id': {'item': 'value'}}
KEYVALUES = {}

# Objects {'id': {'item': 'value'}}
OBJECTS = {}
OBJECTS_RESET = False
OBJECTS_READ_ONLY = False
OBJECTS_TEMPORARY = False


# EMAILS
# ~~~~~~

# E-mails list {'id': {'item': 'value'}}
EMAILS = {}
