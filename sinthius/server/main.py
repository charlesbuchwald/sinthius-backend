#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:30
# ~

import sys
import signal
import logging
from sinthius import compat
from sinthius.conf import settings
from sinthius.utils.logtools import debugcolorizer, trace
from sinthius.utils.terms import colorize
from functools import partial
from tornado import options, ioloop, httpclient, gen, log

# Imported for option definitions
from sinthius.conf import global_options


@gen.coroutine
def initializer(**kwargs):
    debugcolorizer('### SERVICES ###', fg='black', bg='blue')
    logging.info('Initializing services...')

    # Sanitize settings
    if not settings.is_options_parsed():
        options.parse_command_line()
        settings.options_parse(options.options.as_dict())

    # Default Async HTTP Client
    httpclient.AsyncHTTPClient\
        .configure(settings.ASYNC_HTTP_CLIENT, max_clients=100)
    logging.debug(' * Async HTTP Client defined')

    # Happy, Happy, Happy!
    logging.debug('All services initialized')


def run(start_callback, stop_callback=None, _initializer=initializer, **kwargs):
    if not settings.is_options_parsed():
        options.parse_command_line()
        settings.options_parse(options.options.as_dict())

    io_loop = ioloop.IOLoop.current()

    def _on_signal(signum, frame):
        logging.warn(' > Process stopped with signal: %s', signum)
        try:
            stop_callback(**kwargs)
        except:
            io_loop.stop()

    if not compat.WIN:
        signal.signal(signal.SIGHUP, _on_signal)
        signal.signal(signal.SIGQUIT, _on_signal)

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    @gen.coroutine
    def _invoke_callback(wrapped_callback, **config):
        yield gen.Task(wrapped_callback, **config)

    shutdown_by_exception = False

    try:
        level = logging.DEBUG if settings.DEBUG else logging.INFO
        logger = logging.getLogger()
        logger.setLevel(level)

        handler = logger.handlers[0]
        handler.setLevel(level)
        handler.setFormatter(log.LogFormatter())

        logging.info(colorize('### BONJOUR ##########', fg='black', bg='green'))

        io_loop.run_sync(partial(_initializer, **kwargs))
        io_loop.run_sync(partial(_invoke_callback, start_callback))

        if stop_callback is not None:
            io_loop.run_sync(partial(_invoke_callback, stop_callback))

    except Exception, e:
        if not isinstance(e, ioloop.TimeoutError):
            shutdown_by_exception = True
            logging.error(' ! Unhandled exception in %s' % sys.argv[0])
            trace(e)

    if shutdown_by_exception:
        sys.exit(1)

    logging.info(colorize('### AU # REVOIR ######', fg='black', bg='green'))
