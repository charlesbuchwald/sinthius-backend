#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:26
# ~

import logging
from tornado import gen


def no_callback(*args, **kwargs):
    pass


def log_exception_callback(error, value, tback):
    logging.error(' ! Unexpected error', exc_info=(error, value, tback))


def dispatch(response, **kwargs):
    if isinstance(response, Exception):
        raise response
    if 'callback' in kwargs and callable(kwargs['callback']):
        kwargs['callback'](response)
    return response


def dispatch_return(response, **kwargs):
    if isinstance(response, Exception):
        raise response
    if 'callback' in kwargs and callable(kwargs['callback']):
        kwargs['callback'](response)
    else:
        raise gen.Return(response)
