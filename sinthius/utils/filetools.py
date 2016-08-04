#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:27
# ~

import os
import sys
import gzip
from sinthius import compat
from sinthius.errors import FileError, FolderError
from sinthius.utils.decorators import string_or_raise
from contextlib import closing
from imp import load_source
from pip.req import parse_requirements
from tornado import escape


@string_or_raise
def abspath(value, root=None):
    if isinstance(root, compat.string_type):
        value = os.path.join(root, value)
    return os.path.abspath(value)


@string_or_raise
def is_file(value, root=None, raising=True):
    value = abspath(value, root)
    if not os.path.isfile(value):
        if raising:
            raise FileError('File "%s" not found' % value)
        return False
    return value


@string_or_raise
def is_folder(value, root=None, raising=True):
    value = abspath(value, root)
    if not os.path.isdir(value):
        if raising:
            raise FolderError('Folder "%s" not found' % value)
        return False
    return value


def system_paths(path_or_list):
    if isinstance(path_or_list, compat.string_type):
        path_or_list = [path_or_list]
    elif not isinstance(path_or_list, compat.list_type):
        raise RuntimeError('Invalid argument must be a string or list')
    errors = [path for path in path_or_list if not os.path.isdir(path)]
    if errors:
        raise RuntimeError('Paths not found: %s' % ', '.join(errors))
    sys.path.extend(path_or_list)


@string_or_raise
def import_object(value):
    if value.count('.') == 0:
        return __import__(value, None, None)
    package, name = value.rsplit('.', 1)
    value = __import__(package, None, None, [name], 0)
    try:
        return getattr(value, name)
    except AttributeError:
        raise ValueError('No module name "%s"' % name)


def import_settings(value):
    value = is_file(value)
    module = load_source('settings_file', value)
    return {item.lower(): getattr(module, item)
            for item in dir(module) if item.isupper()}


def check_requirements(file_name):
    errors = []
    for item in parse_requirements(file_name):
        item.check_if_exists()
        if not item.satisfied_by:
            errors.append(item)
    if errors:
        errors = [compat.binary_type(e) for e in errors]
        raise RuntimeError('Requirements not installed: %s' % ', '.join(errors))


def gzip_encode(s):
    with closing(compat.StringIO()) as sio:
        with gzip.GzipFile(fileobj=sio, mode='wb') as gz_file:
            gz_file.write(escape.utf8(s))
        return sio.getvalue()


def gzip_decode(s):
    with closing(compat.StringIO(s)) as sio:
        with gzip.GzipFile(fileobj=sio, mode='rb') as gz_file:
            return gz_file.read()
