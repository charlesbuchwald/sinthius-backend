#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:29
# ~

from sinthius.conf import settings
from tornado import options

# settings
options.define('debug', settings.DEBUG)
options.define('track', settings.TRACK)
options.define('ssl', settings.SSL)
options.define('api', settings.API)
options.define('xheaders', settings.XHEADERS)
options.define('xsrf_cookies', settings.XSRF_COOKIES)
options.define('xsrf_cookies_version', settings.XSRF_COOKIES_VERSION)
options.define('ws_xheader_arguments', settings.WS_XHEADER_ARGUMENTS)
options.define('cookie_secret', settings.COOKIE_SECRET)
options.define('compress_response', settings.COMPRESS_RESPONSE)
options.define('autoreload', settings.AUTORELOAD)
options.define('prefork_process', settings.PREFORK_PROCESS)
options.define('async_workers', settings.ASYNC_WORKERS)
options.define('async_http_client', settings.ASYNC_HTTP_CLIENT)
options.define('shutdown_seconds', settings.SHUTDOWN_SECONDS)
options.define('log_max_buffer', settings.LOG_MAX_BUFFER)
options.define('log_flush_interval', settings.LOG_FLUSH_INTERVAL)
options.define('log_error_flush_interval', settings.LOG_ERROR_FLUSH_INTERVAL)
options.define('main', settings.MAIN)
options.define('application', settings.APPLICATION)
options.define('disable_browser', settings.DISABLE_BROWSER)
options.define('ping_response', settings.PING_RESPONSE)
options.define('login_url', settings.LOGIN_URL)
options.define('logout_url', settings.LOGOUT_URL)
options.define('root_url', settings.ROOT_URL)
options.define('locale', settings.LOCALE)
# domain
options.define('ip', settings.IP)
options.define('domain', settings.DOMAIN)
options.define('port', settings.PORT)
# session
options.define('session_id', settings.SESSION_ID)
options.define('session_cookie_id', settings.SESSION_COOKIE_ID)
options.define('session_header_id', settings.SESSION_HEADER_ID)
options.define('session_days', settings.SESSION_DAYS)
options.define('session_seconds', settings.SESSION_SECONDS)
options.define('session_adapter', settings.SESSION_ADAPTER)
options.define('session_serializer', settings.SESSION_SERIALIZER)
options.define('session_secure', settings.SESSION_SECURE)
# objects
options.define('objects_reset', settings.OBJECTS_RESET)
options.define('objects_read_only', settings.OBJECTS_READ_ONLY)
options.define('objects_temporary', settings.OBJECTS_TEMPORARY)

# * Main file definitions:
# ------------------------
# options.define('root_path', None)
# options.define('requirements_file', None)

# * Server base definitions:
# --------------------------
# options.define('server_version', None)
# options.define('server_name', None)
