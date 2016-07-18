#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:20
# ~

import sys
from datetime import date, time, datetime, timedelta

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

try:
    WIN = sys.getwindowsversion()
except:
    WIN = False

if PY2:
    binary_type = str
    text_type = unicode
    string_type = (str, unicode)
    int_type = (int, float)

    try:
        from cStringIO import StringIO
    except:
        from StringIO import StringIO

    try:
        from io import BytesIO
    except:
        BytesIO = StringIO

    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()

else:
    raise RuntimeError('Python 3, not supported yet.-')

# try:
#     import ujson
#     json = ujson
#     json_lib = 'ujson'
#     ujson_available = True
# except:
ujson_available = False
try:
    import simplejson
    json = simplejson
    json_lib = 'simplejson'
except:
    import json
    json_lib = 'json'

try:
    from random import SystemRandom
    random = SystemRandom()
    sys_random = True
except NotImplemented:
    import random
    sys_random = False

try:
    from Crypto.Hash import SHA, SHA256, SHA512, MD5, HMAC
except:
    import hmac
    from hashlib import sha1, sha256, sha512, md5
    SHA = sha1
    SHA256 = sha256
    SHA512 = sha512
    MD5 = md5
    HMAC = hmac

none_type = type(None)
key_type = (string_type, int)
list_type = (tuple, list, set)
iter_type = (tuple, list, set, dict)
datetime_type = (date, time, datetime, timedelta)
primitive_type = (complex, int, float, long, bool, str, basestring, unicode,
                  tuple, list, set)
true_values = (1, '1', 'true', 'yes', 'on', 'ok', 't', 'y')
false_values = (0, '0', 'false', None, 'none', 'null', 'not', 'no', 'f', 'n')
empty = object()
