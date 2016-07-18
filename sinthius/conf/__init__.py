#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:19
# ~

import os
from importlib import import_module
from sinthius import constants, compat
from sinthius.conf import global_settings
from sinthius.errors import ConfigurationError
from sinthius.utils.generators import random_string
from sinthius.utils.lazy import LazyObject


class LazySettings(LazyObject):
    def _setup(self, name=None):
        settings_module = os.environ.get(constants.ENV_SETTINGS_MODULE)
        if not settings_module:
            desc = ('setting %s' % name) if name else 'settings'
            raise ConfigurationError(
                'Requested %s, but settings are not configured. '
                'You must either define the environment variable %s '
                'or call settings.configure() before accessing settings'
                % (desc, constants.ENV_SETTINGS_MODULE))
        self._wrapped = Settings(settings_module)

    def __getattr__(self, name):
        if self._wrapped is compat.empty:
            self._setup(name)
        return getattr(self._wrapped, name)

    def configure(self, default_settings=global_settings, **options):
        if self._wrapped is not compat.empty:
            raise RuntimeError('Settings already configured')
        holder = UserSettingsHolder(default_settings)
        for name, value in options.iteritems():
            setattr(holder, name, value)
        self._wrapped = holder

    def options_parse(self, options):
        if self._wrapped is compat.empty:
            raise RuntimeError('Settings are not configured')
        if not isinstance(options, dict):
            raise ConfigurationError('Options must be a dictionary')
        for key, value in options.iteritems():
            setting_key = key.upper()
            if not hasattr(self._wrapped, setting_key) \
                    or getattr(self._wrapped, setting_key) != value:
                setattr(self._wrapped, setting_key, value)
        self.exec_builders()
        setattr(self._wrapped, constants.ENV_OPTIONS_PARSER, True)

    def is_options_parsed(self):
        return hasattr(self._wrapped, constants.ENV_OPTIONS_PARSER)

    def as_dict(self):
        if self._wrapped is compat.empty:
            raise RuntimeError('Settings are not configured')
        return {item.lower(): getattr(self._wrapped, item)
                for item in dir(self._wrapped)
                if item.isupper() and item != constants.ENV_OPTIONS_PARSER}

    def exec_builders(self):
        self._wrapped.exec_builders()

    @property
    def configured(self):
        return self._wrapped is not compat.empty


class BaseSettings(object):
    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)

    def build_domains(self):
        for key, domain in self.DOMAINS.iteritems():
            if 'port' not in domain or self.PORT != domain['port']:
                domain['port'] = self.PORT

    def build_paths(self):
        if self.ROOT_PATH is None:
            self.ROOT_PATH = '/server'
        self.BIN_PATH = '%s/bin' % self.ROOT_PATH
        self.ETC_PATH = '%s/etc' % self.ROOT_PATH
        self.SRC_PATH = '%s/src' % self.ROOT_PATH
        self.TMP_PATH = '%s/tmp' % self.ROOT_PATH
        self.VAR_PATH = '%s/var' % self.ROOT_PATH
        self.STATIC_PATH = '%s/public/static' % self.VAR_PATH
        self.TEMPLATE_PATH = '%s/template' % self.VAR_PATH
        self.LOCALE_PATH = '%s/locale' % self.VAR_PATH
        self.PATHS = {
            'root': self.ROOT_PATH,
            'bin': self.BIN_PATH,
            'etc': self.ETC_PATH,
            'src': self.SRC_PATH,
            'tmp': self.TMP_PATH,
            'var': self.VAR_PATH,
            'ca': '%s/CA' % self.ETC_PATH,
            'secret': '%s/secret' % self.ETC_PATH,
            'backend': '%s/backend' % self.SRC_PATH,
            'backoffice': '%s/backoffice' % self.SRC_PATH,
            'frontend': '%s/frontend' % self.SRC_PATH,
            'services': '%s/services' % self.SRC_PATH,
            'object': '%s/object' % self.VAR_PATH,
            'otp': '%s/otp' % self.VAR_PATH,
            'public': '%s/public' % self.VAR_PATH,
            'log': '%s/log' % self.VAR_PATH,
            'locale': self.LOCALE_PATH,
            'static': self.STATIC_PATH,
            'template': self.TEMPLATE_PATH
        }
        return self.PATHS

    def exec_builders(self):
        self.build_domains()
        self.build_paths()


class Settings(BaseSettings):
    def __init__(self, settings_module):
        for setting in dir(global_settings):
            if setting.isupper():
                setattr(self, setting, getattr(global_settings, setting))

        self.SETTINGS_MODULE = settings_module
        module = import_module(self.SETTINGS_MODULE)

        list_settings = (
            'HANDLERS',
            'TRANSFORMS',
            'UI_MODULES',
            'UI_METHODS',
            'LOCALE_SUPPORTED'
        )

        dict_settings = (
            'DOMAINS',
            'DATABASES',
            'KEYVALUES',
            'OBJECTS',
            'EMAILS',
        )

        self._explicit_settings = set()

        for setting in dir(module):
            if setting.isupper():
                setting_value = getattr(module, setting)
                if setting in list_settings \
                        and not isinstance(setting_value, compat.list_type):
                    raise ConfigurationError('The "%s" setting must be a list '
                                             'or a tuple. Please fix your '
                                             'settings' % setting)
                if setting in dict_settings \
                        and not isinstance(setting_value, dict):
                    raise ConfigurationError('The "%s" setting must be a dict. '
                                             'Please fix your settings'
                                             % setting)
                setattr(self, setting, setting_value)
                self._explicit_settings.add(setting)

        if not self.SECRET_KEY:
            self.SECRET_KEY = random_string(128)

        self.exec_builders()

    def is_overridden(self, setting):
        return setting in self._explicit_settings


class UserSettingsHolder(BaseSettings):
    SETTINGS_MODULE = None

    def __init__(self, default_settings):
        self.__dict__['_deleted'] = set()
        self.default_settings = default_settings
        self.build_paths()

    def __getattr__(self, name):
        if name in self._deleted:
            raise AttributeError
        return getattr(self.default_settings, name)

    def __setattr__(self, name, value):
        self._deleted.discard(name)
        super(UserSettingsHolder, self).__setattr__(name, value)

    def __delattr__(self, name):
        self._deleted.add(name)
        if hasattr(self, name):
            super(UserSettingsHolder, self).__delattr__(name)

    def __dir__(self):
        return list(self.__dict__) + dir(self.default_settings)

    def is_overridden(self, setting):
        deleted = (setting in self._deleted)
        set_locally = (setting in self.__dict__)
        set_on_default = getattr(
            self.default_settings, 'is_overridden', lambda s: False)(setting)
        return deleted or set_locally or set_on_default


settings = LazySettings()
