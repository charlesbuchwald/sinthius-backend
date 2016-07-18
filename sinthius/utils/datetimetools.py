#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:26
# ~

import time
from datetime import date, datetime, timedelta
from dateutil import parser
from sinthius import constants, compat
from sinthius.utils.typetools import to_string


def datetime_week_range(value=None):
    if not isinstance(value, date):
        value = date.today()
    value = datetime(value.year, value.month, value.day)
    year, week, dow = value.isocalendar()
    ws = value if dow == 7 else value - timedelta(dow)
    we = ws + timedelta(6)
    return ws, we


def datetime_parser(value, default=None):
    kwargs = {}
    if isinstance(value, compat.datetime_type):
        return value
    elif isinstance(value, compat.list_type):
        value = ' '.join([to_string(x) for x in value])
    elif isinstance(value, (long,) + compat.int_type):
        value = to_string(value)
    elif isinstance(value, dict):
        kwargs = value
        value = kwargs.pop('date')
    try:
        try:
            value = parser.parse(value, **kwargs)
        except ValueError:
            value = parser.parse(value, fuzzy=True, **kwargs)
        return value
    except:
        return default or datetime.utcnow()


def uptime_calculate(start, check=None):
    if check is None or not isinstance(check, float):
        check = time.time()
    uptime = check - start
    days, seconds = uptime // constants.SECONDS_PER_DAY, \
                    uptime % constants.SECONDS_PER_DAY
    hours, seconds = seconds // constants.SECONDS_PER_HOUR, \
                     seconds % constants.SECONDS_PER_HOUR
    minutes, seconds = seconds // constants.SECONDS_PER_MINUTE, \
                       seconds % constants.SECONDS_PER_MINUTE
    return {
        'uptime': {
            'start': datetime.utcfromtimestamp(start),
            'check': datetime.utcfromtimestamp(check),
            'info': {
                'days': int(days),
                'hours': int(hours),
                'minutes': int(minutes),
                'seconds': int(seconds)
            }
        },
        'epoch': {
            'start': start,
            'check': check,
            'uptime': uptime
        }
    }
