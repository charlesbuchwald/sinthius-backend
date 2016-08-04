#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 13/jun/2016 09:24
# ~

import validictory
from sinthius.errors import MessageError
from functools import partial


class Message(object):
    MIN_VERSION = 0
    MAX_VERSION = 100
    ADD_HEADERS_VERSION = 1

    _VERSION_HEADER_SCHEMA = {
        'description': 'defines message with optional headers object',
        'type': 'object',
        'properties': {
            'headers': {
                'description': 'defines headers object with required version '
                               'field',
                'type': 'object',
                'properties': {
                    'version': {
                        'description': 'version of the message format',
                        'type': 'integer',
                        'minimum': ADD_HEADERS_VERSION,
                    },
                    'min_version': {
                        'description': 'minimum required message format '
                                       'version that must be supported by '
                                       'the server',
                        'type': 'integer',
                        'required': False,
                        'minimum': MIN_VERSION
                    }
                },
            },
        }
    }

    def __init__(self, message, min_version=MIN_VERSION,
                 max_version=MAX_VERSION, default_version=MIN_VERSION):
        if not isinstance(message, dict):
            raise MessageError('Message must be a dictionary')
        self._message = message
        self._schema = None
        if min_version < MIN_VERSION or max_version > MAX_VERSION:
            raise MessageError('The "min version" must be greater than or '
                               'equal to "%s" and the "max version" less than '
                               'or equal to "%s"' % (MIN_VERSION, MAX_VERSION))
        self._original_version = self._get_version(max_version, default_version)
        self._version = self._original_version
        if self.version > max_version:
            raise MessageError('Version "%s" of this message is not supported '
                               'by the server. The server only support this '
                               'message up to version "%s".'
                               % (self.version, max_version))
        if self.version < min_version:
            raise MessageError('Version "%s" of this message is not supported '
                               'by the server. The server only support this '
                               'message starting at version "%s"'
                               % (self.version, min_version))

    @property
    def message(self):
        return self._message

    @property
    def schema(self):
        return self._schema

    @property
    def version(self):
        return self._version

    @property
    def original_version(self):
        return self._original_version

    def validate(self, schema, allow_extra_fields=False):
        if schema is None:
            raise MessageError('A schema must be provided in order to validate')
        try:
            validictory.validate(self._message, schema)
            if not allow_extra_fields:
                self._find_extra_fields(self._message, schema, True)
            self._schema = schema
        except Exception, e:
            raise MessageError(e.message)

    def sanitize(self):
        if self._schema is None:
            raise MessageError('No schema available. Sanitize may only be '
                               'called after Validate has been called')
        self._find_extra_fields(self._message, self._schema, False)

    def migrate(self, client, version, callback, migrators=None):
        def _on_migrate(intermediate):
            self._version = intermediate
            if intermediate >= Message.ADD_HEADERS_VERSION:
                self._message['headers']['version'] = intermediate
            self.migrate(client, version, callback, migrators)

        if version < MIN_VERSION or version > MAX_VERSION:
            raise MessageError('The "min version" must be greater than or '
                               'equal to "%s" and the "max version" less than '
                               'or equal to "%s"' % (MIN_VERSION, MAX_VERSION))
        if migrators is None:
            migrators = REQUIRED_MIGRATORS
        count = len(migrators)
        if count > 0 and not isinstance(migrators[0], AddHeadersMigrator):
            raise MessageError('The first migrator is not AddHeadersMigrator. '
                               'Did you forget to merge with '
                               'REQUIRED_MIGRATORS and sort?')
        if self.version == version:
            callback(self)
            return
        if self.version < version:
            for item in xrange(count):
                migrator = migrators[item]
                assert item == 0 \
                    or migrators[item - 1].version < migrator.version
                if migrator.version > version:
                    break
                if self.version < migrator.version:
                    func = partial(_on_migrate, migrator.version)
                    migrator.forward(client, self, func)
                    return
        else:
            for item in xrange(count, 0, -1):
                migrator = migrators[item - 1]
                assert item == count \
                    or migrators[item].version > migrator.version
                if migrator.version <= version:
                    break
                if self.version >= migrator.version:
                    func = partial(_on_migrate, migrator.version - 1)
                    migrator.backward(client, self, func)
                    return
        _on_migrate(version)

    def visit(self, visitor):
        self._visit_helper(self._message, visitor)

    def _visit_helper(self, message, visitor):
        if isinstance(message, dict):
            for key, value in message.items():
                self._visit_helper(value, visitor)
                result = visitor(key, value)
                if result is None:
                    continue
                del message[key]
                if len(result) == 2:
                    message[result[0]] = result[1]
        elif isinstance(message, list):
            for item in message:
                self._visit_helper(item, visitor)

    def _find_extra_fields(self, message, schema, raise_error):
        if schema['type'] == 'object':
            if not isinstance(message, dict):
                raise MessageError('The value must be a dictionary')
            for key in message.keys():
                if 'properties' in schema:
                    properties = schema['properties']
                    if key not in properties:
                        if raise_error:
                            raise MessageError('Message contains field "%s", '
                                               'which is not present in the '
                                               'schema' % key)
                        else:
                            del message[key]
                        continue
                    if properties[key]['type'] in ('object', 'array'):
                        self._find_extra_fields(
                            message[key], properties[key], raise_error)
        elif schema['type'] == 'array':
            if not isinstance(message, list):
                raise MessageError('The value must be a list')
            for value in message:
                self._find_extra_fields(value, schema['items'], raise_error)

    def _get_version(self, max_version, default_version):
        headers = self._message.get('headers', None)
        if headers is None:
            if default_version == Message.MIN_VERSION:
                return Message.MIN_VERSION
            self._message['headers'] = {'version': default_version}
        elif 'version' not in headers:
            headers['version'] = default_version
        try:
            validictory.validate(self._message, Message._VERSION_HEADER_SCHEMA)
        except Exception, e:
            raise MessageError(e.message)
        version = int(self._message['headers']['version'])
        if 'min_version' in self._message['headers']:
            min_version = int(self._message['headers']['min_version'])
            if min_version > version:
                raise MessageError('The "min_version" value (%s) cannot be '
                                   'greater than the "version" value (%s)'
                                   % (min_version, version))
            if version > max_version:
                version = max(min_version, max_version)
        return version


class MessageMigrator(object):
    def __init__(self, version):
        self.version = version

    def forward(self, client, message, callback):
        raise NotImplementedError()

    def backward(self, client, message, callback):
        raise NotImplementedError()

    def __cmp__(self, other):
        if not isinstance(other, MessageMigrator):
            raise MessageError('Other must be a "MessageMigrator" instance')
        return cmp(self.version, other.version)


class AddHeadersMigrator(MessageMigrator):
    def __init__(self):
        super(AddHeadersMigrator, self).__init__(Message.ADD_HEADERS_VERSION)

    def forward(self, client, message, callback):
        message.message['headers'] = {'version': Message.ADD_HEADERS_VERSION}
        callback()

    def backward(self, client, message, callback):
        del message.message['headers']
        callback()


REQUIRED_MIGRATORS = [AddHeadersMigrator()]
MIN_VERSION = Message.MIN_VERSION
MAX_VERSION = Message.MAX_VERSION
