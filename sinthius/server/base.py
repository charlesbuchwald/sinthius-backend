#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:30
# ~

import time
import logging
from sinthius import constants, compat
from sinthius.conf import settings
from sinthius.utils.filetools import import_object
from sinthius.utils.logtools import debugcolorizer
from sinthius.utils.serializers import jsondumps
from sinthius.utils.terms import jsoncolorize
from sinthius.utils.versiontools import ObjectVersion
from sinthius.web.application import ServerApplication
from functools import partial
from tornado import options, httpserver, ioloop, stack_context, gen

# Imported for option definitions
from sinthius.conf import global_options

__SERVER = None
__project_name__ = 'CPS'
__project_full_name__ = 'SINTHIUS Python Server'
__project_owner__ = ('Asumi Kamikaze, inc',)
__project_author__ = ('Alejandro M. Bernardis',)
__project_created__ = (2016, 6)
__project_modified__ = (2016, 6)

# Versions schema:
#  * 1.0 (production)
#  * 1.0.dev (development)
#  * 1.0.sta (staging)
options.define('server_version', '1.0.dev')
options.define('server_name', 'astor-piazzolla')


class ServerEnvironment(object):
    def __init__(self, name, application, http_server, loop, version=None):
        self._name = name
        self._application = application
        self._server = http_server
        self._loop = loop
        self._version = ObjectVersion(version or settings.SERVER_VERSION)

    @property
    def name(self):
        return self._name

    @property
    def server(self):
        return self._server

    @property
    def application(self):
        return self._application

    @property
    def loop(self):
        return self._loop

    @property
    def version(self):
        return self._version

    @property
    def is_staging(self):
        return 'sta' in self.version.components

    @property
    def is_development(self):
        return 'dev' in self.version.components

    @property
    def is_production(self):
        return not all([self.is_development, self.is_staging])

    def __str__(self):
        return '<Server("%s"): %s>' % (self.name, self.version.value)

    def __repr__(self):
        return self.__str__()


def server():
    global __SERVER
    if __SERVER is None:
        raise RuntimeError('The server has not been initialized yet')
    return __SERVER


@gen.coroutine
def start_server(*args, **kwargs):
    global __SERVER
    debugcolorizer('### SERVER ###', fg='black', bg='blue')
    logging.info('Starting server...')

    if not settings.is_options_parsed():
        options.parse_command_line()
        settings.options_parse(options.options.as_dict())

    settings_dict = settings.as_dict()

    try:
        module = None
        for key in constants.APPLICATION_CLASS_LIST:
            if key in settings_dict:
                cls = settings_dict[key]
                module = import_object(cls)
                break
        application = module(**settings_dict)
    except:
        application = ServerApplication(**settings_dict)

    if settings.DEBUG:
        code = jsoncolorize(jsondumps(settings_dict, indent=2, sort_keys=True))
        logging.debug(' * Settings:\n\n%s\n\n', code)

    http_server = httpserver.HTTPServer(application, **{
        'xheaders': settings.XHEADERS,
        'ssl_options': application.ssl_options
    })

    io_loop = ioloop.IOLoop.current()
    application.set_exit_callback(partial(_stop_loop, io_loop))

    with stack_context.NullContext():
        if settings.PREFORK_PROCESS > -1:
            http_server.bind(settings.PORT)
            http_server.start(settings.PREFORK_PROCESS)
        else:
            http_server.listen(settings.PORT)

    yield gen.Task(application.start)

    __SERVER = ServerEnvironment(
        settings.SERVER_NAME, application, http_server, io_loop)

    url = 'http://{domain}:{port}'.format(**settings_dict)
    logging.info('%s v%s', __SERVER.name.upper(), __SERVER.version.value)
    logging.info('Running server on %s', url)
    logging.info('--')

    if not compat.WIN and settings.DEBUG and not settings.DISABLE_BROWSER:
        import subprocess
        subprocess.Popen(['open', url])

    yield gen.Task(lambda callback: None)


def _stop_loop(loop):
    logging.debug(' * Stopping loop...')
    loop.stop()
    logging.info('Shutdown server')


@gen.coroutine
def stop_server(*args, **kwargs):
    debugcolorizer('### SERVER ###', fg='black', bg='blue')
    logging.warn('Shutting down server...')

    env = server()

    logging.debug(' * Stopping server...')
    yield env.server.close_all_connections()
    env.server.stop()

    logging.debug(' * Stopping application...')
    yield env.application.shutdown()

    logging.debug(' * Setting timeout...')
    seconds = time.time() + settings.SHUTDOWN_SECONDS
    env.loop.add_timeout(seconds, partial(_stop_loop, env.loop))
