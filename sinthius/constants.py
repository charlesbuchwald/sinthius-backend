#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:20
# ~

ENV_OPTIONS_PARSER = 'OPTIONS_PARSER'
ENV_SETTINGS_MODULE = 'SETTINGS_MODULE'
APPLICATION_CLASS_LIST = ('application', 'application_class')
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 60 * 60
SECONDS_PER_DAY = 60 * 60 * 24
SECONDS_PER_WEEK = SECONDS_PER_DAY * 7
SECONDS_PER_MONTH = SECONDS_PER_WEEK * 4
PRIMITIVE_METHODS = ('to_python', 'to_object', 'to_dict', 'to_mongo',
                     'to_mongodb', 'to_primitive')
BINARY_SERIALIZER = ('marshal', 'msgpack', 'umsgpack')
JSON_SERIALIZER = ('json', 'simplejson')  # , 'ujson')
PYTHON_SERIALIZER = ('pickle', 'cPickle')
SERIALIZERS = BINARY_SERIALIZER + JSON_SERIALIZER + PYTHON_SERIALIZER
ASCII = 'ascii'
LATIN1 = 'latin-1'
UTF8 = 'utf-8'
ENCODING = UTF8
LOCALE = 'en_US'
DEFAULT_KEY = 'default'
LOCALHOST = 'localhost'
