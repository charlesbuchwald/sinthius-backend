#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:27
# ~

import os
import string
from bson import ObjectId
from sinthius import compat
from sinthius.utils.binary import want_bytes
from datetime import datetime, time

DEFAULT_LENGTH = 64


def random_string(length=DEFAULT_LENGTH):
    h = string.ascii_letters + string.digits + string.punctuation \
        + datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    if not compat.sys_random:
        compat.random.seed(compat.SHA256.new(want_bytes(
            ('%s%s%s' % compat.random.getstate(), time.time(), os.urandom(32))
        )).digest())
    return ''.join([compat.random.choice(h) for _ in xrange(length)])


def object_id():
    return ObjectId().__str__()
