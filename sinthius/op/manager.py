#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 13/jun/2016 09:20
# ~

import copy
from sinthius.utils.dicttools import DotDict
from sinthius.utils.decorators import key_type_or_error
from sinthius.utils.filetools import import_object
from sinthius import compat
from sinthius.errors import ManagerError, FactoryError
from functools import partial


class DictManager(dict):
    """
    Example:
    --------
    .. code-block:: python
        def factory(value, supported, ..., *args, **kwargs):
            if value not in supported:
                raise ValueError()
    """
    def __init__(self, name, description=None, factory_method=None, **kwargs):
        super(DictManager, self).__init__()
        self.name = name
        self.description = description
        self.factory_method = None if factory_method is None \
            else partial(factory_method, **kwargs)

    @key_type_or_error
    def put(self, key, method=None, **kwargs):
        if key in self:
            raise ManagerError('Cannot override a key: "%s"' % key)
        method = method or self.factory_method
        if callable(method):
            self[key] = method(**kwargs)
        else:
            raise ManagerError('The factory method must be callable or a class')


class DotDictManager(DotDict):
    def __init__(self, name, description=None, factory_method=None, **kwargs):
        super(DotDictManager, self).__init__()
        self.name = name
        self.description = description
        self.factory_method = None if factory_method is None \
            else partial(factory_method, **kwargs)

    @key_type_or_error
    def put(self, key, method=None, **kwargs):
        if key in self:
            raise ManagerError('Cannot override a key: "%s"' % key)
        method = method or self.factory_method
        if callable(method):
            self[key] = method(**kwargs)
        else:
            raise ManagerError('The factory method must be callable or a class')


def factory(name=None, options=None, module=None, settings=None, **kwargs):
    """
    Example:
    --------
    .. code-block:: python

        options = {
            'session': {
                'module': 'path.to.module',
                'settings': {
                    ...
                }
            },
            'cache': 'path.to.module'
        }

        module = factory('session', options)

        # settings or keywords argument

        settings = {
            'name': 'sid',
            'secure_cookie': True,
            'adapter': {
                'port': 11211,
                'domain': 'localhost'
            }
        }

        module = factory(module='path.to.module', settings=settings)

    :param name: (string)
    :param options: (dict)
    :param settings: (dict)
    :param module: (string or instance)
    :param kwargs:
    :return:
    """
    if module is None:
        if isinstance(name, compat.string_type) and isinstance(options, dict):
            if name not in options:
                raise FactoryError('Option not supported: %s' % name)
            else:
                opts = options[name]
                if isinstance(opts, dict) and 'module' in opts:
                    module = opts['module'] or module
                    try:
                        settings = opts['settings']
                    except:
                        settings = settings
                elif isinstance(opts, compat.string_type):
                    module = opts
                else:
                    raise FactoryError(
                        'Please define into your "options" a dictionary '
                        'with a {"name": "path.to.module"} or '
                        '{"name": {"module": "module.to.path", "settings": {}}}'
                    )
        else:
            raise FactoryError('Bad configuration, you need to define the '
                               'argument "name" with "options" and/or '
                               '"settings", or maybe "module" and "settings"')

    if isinstance(module, compat.string_type):
        module = import_object(module)

    if not callable(module):
        raise FactoryError('The module must be callable or an object instance')

    if settings:
        kwargs.update(settings)

    return module(**kwargs)


def purge_settings(settings, values=None):
    if values is None or not isinstance(values, compat.list_type):
        return settings
    settings = copy.deepcopy(settings)
    for key in settings.keys():
        if key not in values:
            del settings[key]
    return settings
