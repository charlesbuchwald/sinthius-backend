#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:29
# ~

import os
import re
import time
from sinthius import compat
from sinthius.conf import settings as global_settings
from sinthius.errors import ConfigurationError
from sinthius.web.base import NotFoundHandler, APINotFoundHandler
from sinthius.utils.binary import want_bytes
from sinthius.utils.dicttools import setdefault
from sinthius.utils.datetimetools import uptime_calculate
from sinthius.utils.filetools import is_file, is_folder, import_object
from sinthius.utils.generators import random_string
from functools import wraps
from tornado import web, gen, locale

DEFAULT_HOST = '.*$'
DEFAULT_HOST_END = '$'
DEFAULT_CONTAINER = 'handlers_list'


def handlers_args_sanitize(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        args = list(args)
        value = kwargs.get('host_pattern', args[0])
        if not value:
            value = DEFAULT_HOST
        if not value.endswith(DEFAULT_HOST_END):
            value += DEFAULT_HOST_END
        args[0] = value
        value = kwargs.get('host_handlers', args[1])
        if isinstance(value, compat.string_type):
            args[1] = [want_bytes(value)]
        elif not isinstance(value, compat.list_type):
            raise ConfigurationError('Invalid argument type, "host_pattern" '
                                     'must be a string or a list')
        return method(self, *args, **kwargs)
    return wrapper


class ServerApplication(web.Application):
    def __init__(self, **settings):
        setdefault(settings, 'cookie_secret', random_string(128))
        settings['ui_modules'] = \
            self._parse_ui_elements(settings.get('ui_modules', {}))
        settings['ui_methods'] = \
            self._parse_ui_elements(settings.get('ui_methods', {}))
        settings['transforms'] = \
            self._parse_transforms(settings.get('transforms', None))
        locale_path = is_folder(settings['locale_path'])
        if len(os.listdir(locale_path)):
            locale.load_gettext_translations(locale_path, settings['domain'])
        handlers = []
        if settings.get('handlers', False):
            handlers.extend(self._parse_handlers_list(settings['handlers']))
        not_found_handler = NotFoundHandler if not settings['api'] \
            else APINotFoundHandler
        handlers.append((r'/.*', not_found_handler))
        if 'handlers' in settings:
            del settings['handlers']
        super(ServerApplication, self).__init__(handlers, **settings)
        self._start_time = time.time()

    # handlers

    def _parse_handlers_list(self, module_or_list):
        result = []
        for item in module_or_list:
            if isinstance(item, compat.list_type) and len(item) in (2, 3, 4):
                result.append(item)
            elif isinstance(item, compat.string_type):
                values = import_object('%s.%s' % (item, DEFAULT_CONTAINER))
                if not isinstance(values, compat.list_type):
                    raise ConfigurationError(
                        'Module "%s" does not define "%s" attribute like a list'
                        % (item, DEFAULT_CONTAINER))
                result.extend(values)
            else:
                raise ConfigurationError('Element not supported: %s' % item)
        return result

    def _parse_handlers_urlspec(self, handlers_list):
        result = []
        for item in handlers_list:
            if isinstance(item, web.URLSpec):
                result.append(item)
            elif isinstance(item, compat.list_type) and len(item) in (2, 3, 4):
                item = web.URLSpec(*item)
                result.append(item)
                if item.name:
                    self.named_handlers[item.name] = item
            else:
                raise ConfigurationError('Element not supported: %s' % item)
        return result

    def _parse_handlers_host(self, host_pattern):
        if host_pattern == DEFAULT_HOST:
            return len(self.handlers) - 1
        index = [i for i, e in enumerate(self.handlers)
                 if e[0].pattern == host_pattern]
        return -1 if not index else index[0]

    @handlers_args_sanitize
    def add_handlers(self, host_pattern, host_handlers):
        handlers = self._parse_handlers_urlspec(host_handlers)
        if self.handlers:
            index = self._parse_handlers_host(host_pattern)
            if index > -1:
                host, values = self.handlers[index]
                self.handlers[index] = (host, list(set(values) | set(handlers)))
            else:
                self.handlers.insert(0, (re.compile(host_pattern), handlers))
        else:
            self.handlers.append((re.compile(host_pattern), handlers))

    @handlers_args_sanitize
    def remove_handlers(self, host_pattern, host_handlers):
        index = self._parse_handlers_host(host_pattern)
        if not self.handlers or index < 0:
            raise ConfigurationError('Host not supported: %s' % host_pattern)
        host, values = self.handlers[index]
        handlers = self._parse_handlers_urlspec(host_handlers)
        self.handlers[index] = (host, list(set(values) ^ set(handlers)))

    # transforms

    def _parse_transforms(self, module_or_list):
        if not module_or_list:
            return []
        elif isinstance(module_or_list, compat.string_type):
            module_or_list = [module_or_list]
        return [import_object(item) for item in module_or_list]

    def add_transform(self, module_or_list):
        if isinstance(module_or_list, compat.list_type):
            self.transforms.extends(self._parse_transforms(module_or_list))
        else:
            if isinstance(module_or_list, compat.string_type):
                module_or_list = import_object(module_or_list)
            super(ServerApplication, self).add_transform(module_or_list)

    # ui modules and methods

    def _parse_ui_elements(self, module_or_list):
        if not module_or_list:
            return {}
        elif isinstance(module_or_list, compat.string_type):
            module_name = module_or_list.split('.')[-1]
            module_or_list = {module_name: module_or_list}
        return {k: import_object(v) for k, v in module_or_list.iteritems()}

    def add_ui_modules(self, module_or_list):
        self._load_ui_modules(self._parse_ui_elements(module_or_list))

    def add_ui_methods(self, module_or_list):
        self._load_ui_methods(self._parse_ui_elements(module_or_list))

    # debug

    @property
    def debug(self):
        try:
            return self.settings.get('debug', global_settings.DEBUG)
        except:
            return False

    # ssl

    @property
    def ssl_options(self):
        import ssl
        if self.settings.get('ssl', False):
            ca_path = self.settings.get('ca_path', '/etc/ssl/certs')
            return {
                'cert_reqs': ssl.CERT_REQUIRED,
                'ca_certs': is_file('cacert.crt', ca_path),
                'certfile': is_file('server.crt', ca_path),
                'keyfile': is_file('server.key', ca_path)
            }
        return None

    # stats

    def stats(self, add_settings=None, **kwargs):
        if add_settings or self.settings.get('debug', False):
            kwargs.setdefault('elements', {
                'handlers': {
                    'total': len(self.handlers[0][1]),
                    'paths': [i.regex.pattern for i in self.handlers[0][1]],
                },
                'named_handlers': {
                    'total': len(self.named_handlers)
                },
                'transforms': {
                    'total': len(self.transforms)
                },
                'ui_modules': {
                    'names': self.ui_modules.keys(),
                    'total': len(self.ui_modules)
                },
                'ui_methods': {
                    'names': self.ui_methods.keys(),
                    'total': len(self.ui_methods)
                }
            })
            kwargs.setdefault('default_host', self.default_host)
            kwargs.setdefault('settings', self.settings)
            kwargs.setdefault('ssl_options', self.ssl_options)
        return self.uptime(**kwargs)

    def uptime(self, **kwargs):
        kwargs.setdefault('uptime', uptime_calculate(self._start_time))
        return kwargs

    # start

    @gen.coroutine
    def start(self, **kwargs):
        raise gen.Return()

    # shutdown

    def set_exit_callback(self, callback):
        setattr(self, '_exit_callback', callback)

    def exit_callback(self):
        callback = getattr(self, '_exit_callback')
        if callable(callback):
            callback()

    @gen.coroutine
    def shutdown(self, **kwargs):
        raise gen.Return()
