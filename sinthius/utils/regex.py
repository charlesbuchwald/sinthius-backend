#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:28
# ~

import re

rx_camel_case_split = re.compile(
    r'((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')
rx_locale_delimiter = re.compile(
    r'[_-]')
rx_template_name = re.compile(
    r'(handler|action|controller)', re.I)
rx_text_plain = re.compile(
    r'^text(_?plain)?$', re.I)
rx_valid_char = re.compile(
    r'^[a-z0-9_-]*={0,3}$', re.I)
rx_uuid = re.compile(
    r'(?i)(?<![a-z0-9])[0-f]{8}(?:-[0-f]{4}){3}-[0-f]{12}(?![a-z0-9])', re.I)
rx_isoformat = re.compile(
    r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[0-1]|0[1-9]|[1-2][0-9])?'
    r'T(2[0-3]|[0-1][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)??'
    r'(Z|[+-](?:2[0-3]|[0-1][0-9]):[0-5][0-9])?$', re.I)
rx_isoformat_date = re.compile(
    r'^([0-9]{4})(?:(1[0-2]|0[1-9])|-?(1[0-2]|0[1-9])-?)?'
    r'(3[0-1]|0[1-9]|[1-2][0-9])$', re.I)
rx_isoformat_time = re.compile(
    r'^(2[0-3]|[0-1][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)??'
    r'(Z|[+-](?:2[0-3]|[0-1][0-9]):[0-5][0-9])?$', re.I)
rx_datetime_marker = re.compile(
    r'(UTC|GMT)', re.I)
rx_integer = re.compile(
    r'^-?[0-9]+$')
rx_float = re.compile(
    r'^-?[0-9]+\.[0-9]+$')
rx_long = re.compile(
    r'^-?[0-9]+L$', re.I)
rx_sid = re.compile(
    r'(?i)(?<![0-9a-f])([0-9a-f]{4,12}\-?)+(?![0-9a-f])', re.I)
rx_sid_1664 = re.compile(
    r'(?i)(?<![a-z0-9])([0-9a-z]{16,64}\-?)+(?![a-z0-9])', re.I)
