#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:26
# ~

import base64
import string
import struct
from sinthius import constants, compat
from sinthius.utils.decorators import value_or_none
from sinthius.utils.regex import rx_valid_char
from tornado import escape


@value_or_none
def want_bytes(value, encoding=constants.ENCODING, errors='strict'):
    if isinstance(value, compat.text_type):
        value = value.encode(encoding, errors)
    return compat.binary_type(value)


@value_or_none
def force_bytes(value, encoding=constants.ENCODING, strings_only=False,
                errors='strict'):
    if isinstance(value, bytes):
        if encoding == constants.ENCODING:
            return value
        else:
            return value.decode(constants.ENCODING, errors)\
                .encode(encoding, errors)
    if isinstance(value, buffer):
        return bytes(value)
    if not isinstance(value, compat.string_type):
        try:
            return bytes(value)
        except UnicodeEncodeError:
            if isinstance(value, Exception):
                data = [force_bytes(arg, encoding, strings_only, errors)
                        for arg in value]
                return b' '.join(data)
            return compat.text_type(value).encode(encoding, errors)
    else:
        return value.encode(encoding, errors)


_std_alphabet = '%s%s%s+/' % (string.uppercase, string.lowercase, string.digits)
_hex_alphabet = '-%s%s_%s' % (string.digits, string.uppercase, string.lowercase)
_to_hex = string.maketrans(_std_alphabet, _hex_alphabet)
_to_std = string.maketrans(_hex_alphabet, _std_alphabet)


def base64_hex_encode(value, padding=True):
    encoded = base64.b64encode(value)
    translated = encoded.translate(_to_hex)
    if padding:
        return translated
    else:
        return translated.rstrip('=')


def base64_hex_decode(value, padding=True):
    value = escape.utf8(value)
    if not rx_valid_char.match(value):
        raise TypeError('Invalid characters')
    pad_needed = len(value) % 4
    if pad_needed:
        if padding:
            raise TypeError('Invalid padding')
        else:
            value += '=' * pad_needed
    translated = value.translate(_to_std)
    return base64.b64decode(translated)


def pack_sort_key_prefix(timestamp, randomness=True, reverse=False):
    assert timestamp < 1L << 32, timestamp
    if reverse:
        timestamp = (1L << 32) - int(timestamp) - 1
    random_bits = compat.random.getrandbits(16) & 0xffff if randomness else 0
    return base64_hex_encode(struct.pack('>IH', int(timestamp), random_bits))


def unpack_sort_key_prefix(prefix):
    timestamp, random_bits = struct.unpack('>IH', base64_hex_decode(prefix))
    return timestamp


def encode_var_length_number(value):
    byte_str = ''
    while value >= 128:
        byte_str += struct.pack('>B', (value & 127) | 128)
        value >>= 7
    byte_str += struct.pack('>B', value & 127)
    return byte_str


def decode_var_length_number(str_byte):
    value = 0
    num_bytes = 0
    for shift in xrange(0, 64, 7):
        byte, = struct.unpack('>B', str_byte[num_bytes:num_bytes + 1])
        num_bytes += 1
        if byte & 128:
            value |= ((byte & 127) << shift)
        else:
            value |= (byte << shift)
            return value, num_bytes
    raise TypeError('String not decodable as variable length number')


def pack_location(latitude, longitude, accuracy):
    values = (latitude, longitude, accuracy)
    return base64_hex_encode(struct.pack('>ddd', *[float(x) for x in values]))


def unpack_location(value):
    return struct.unpack('>ddd', base64_hex_decode(value))


def pack_placemark(iso_country, country, state, locality, postal_code):
    values = [base64_hex_encode(compat.binary_type(want_bytes(item)), False)
              for item in (iso_country, country, state, locality, postal_code)]
    return ','.join(values)


def unpack_placemark(values):
    result = []
    for item in values.split(','):
        try:
            value = base64_hex_decode(item.rstrip('='), False)\
                .decode(constants.ENCODING)
        except:
            value = ''
        result.append(value)
    return result
