#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:28
# ~

from __future__ import unicode_literals

import re
from sinthius.errors import SMSError
from functools import wraps
from tornado import escape, gen

GSM_GOOD = u'@£$¥èéùìòÇ\nØø\rÅå_ÆæßÉ !"#%&\'()*+,-./0123456789:;<=>?¡' \
           u'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà'

GSM_BAD = u'¤ΔΦΓΛΩΠΨΣΘΞ'
MAX_GSM_CHARS = 160
MAX_UTF16_CHARS = 70

rx_good_chars = re.compile(u'^[%s]*$' % re.escape(GSM_GOOD))
rx_bad_chars = re.compile(u'^[%s]*$' % re.escape(GSM_BAD))
rx_force_unicode = re \
    .compile(u'^[%s%s]*$' % (re.escape(GSM_BAD), re.escape(GSM_GOOD)))


def force_unicode(value):
    value = escape.to_unicode(value)
    return rx_force_unicode.search(value) and not rx_good_chars.search(value)


def is_one_sms_message(value):
    value = escape.to_unicode(value)
    utf16_count = len(value.encode('utf-16-be')) / 2
    if rx_bad_chars.search(value):
        return utf16_count <= MAX_GSM_CHARS
    return utf16_count <= MAX_UTF16_CHARS


def is_message(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        message = kwargs.get('message', args[1])
        if not force_unicode(message) or not is_one_sms_message(message):
            raise gen.Return(SMSError('Message not supported'))
        return method(self, *args, **kwargs)
    return wrapper
