#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 13/jun/2016 09:42
# ~

import os
from sinthius.conf import settings as global_settings
from sinthius.drivers.base import SerializerAbstract, _parse_arguments
from sinthius.utils.async import dispatch
from sinthius.utils.filetools import abspath
from functools import wraps


def verify_filename(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        filename = kwargs.get('filename')
        if not filename:
            if not self.filename:
                raise ValueError('The file name is not defined')
            kwargs['filename'] = self.filename
        result = method(self, *args, **kwargs)
        if 'callback' in kwargs:
            kwargs['callback'](result)
        else:
            return result
    return wrapper


class DocumentClient(SerializerAbstract):
    def __init__(self, filename=None, settings=None, read_only=False):
        self._data = None
        self._filename = None

        if filename is None:
            if 'filename' in settings:
                filename = settings['filename']
                del settings['filename']
            else:
                filename = 'default.file'

        root = settings.get('root', '{tmp}').format(**global_settings.PATHS)
        self.filename = '%s/%s' % (root, filename)

        if settings.get('makefile', False) is True:
            if not os.path.isdir(root):
                os.makedirs(root)
            if not os.path.isfile(self.filename):
                open(self.filename, 'w+').close()

        settings = _parse_arguments(self, settings, (
            ('serializer', False, 'cPickle'),
        ))

        super(DocumentClient, self).__init__(settings, read_only)
        self._make_serializer()

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = abspath(value)

    @property
    def data(self):
        return self._data

    @verify_filename
    def fetch(self, **kwargs):
        with open(kwargs['filename'], 'r+b') as f_input:
            self._data = self._loads(f_input.read())
        return dispatch(self._data, **kwargs)

    @verify_filename
    def save(self, data, **kwargs):
        if data is not None:
            self.force_save(data, kwargs['filename'], **kwargs)
        return dispatch(self._data, **kwargs)

    @verify_filename
    def force_save(self, data, **kwargs):
        with open(kwargs['filename'], 'w+b') as f_output:
            f_output.write(self._dumps(data))
        self._data = data
        return dispatch(self._data, **kwargs)

    @verify_filename
    def delete(self, *args, **kwargs):
        try:
            os.remove(kwargs['filename'])
            self._data = None
            response = True
        except:
            response = False
        return dispatch(response, **kwargs)


def get_connector(async=False):
    return DocumentClient


def get_client(config, arguments=None, async=None):
    if async is None:
        async = config.get('async', False)
    client = get_connector(async)
    return client(**config)
