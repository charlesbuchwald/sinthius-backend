#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:27
# ~

import base64
from functools import wraps
from sinthius import compat
from sinthius.constants import ENCODING


# def value_or_none(func):
#     def decorator(value, *args, **kwargs):
#         if value is None:
#             return None
#         return func(value, *args, **kwargs)
#     return decorator
#
#
# def string_or_none(func):
#     def decorator(value, *args, **kwargs):
#         if not isinstance(value, compat.string_type):
#             return None
#         return func(value, *args, **kwargs)
#     return decorator
#
#
# def value_or_raise(message):
#     def decorator(func):
#         @wraps(func)
#         def wrapper(value, *args, **kwargs):
#             if value is None:
#                 text = message if isinstance(message, compat.string_type) \
#                     else 'The value must be a object.'
#                 raise ValueError(text)
#             func(value, *args, **kwargs)
#         return wrapper
#     if callable(message):
#         return decorator(message)
#     return decorator
#
#
# def string_or_raise(message):
#     def decorator(func):
#         @wraps(func)
#         def wrapper(value, *args, **kwargs):
#             if not isinstance(value, compat.string_type):
#                 text = message if isinstance(message, compat.string_type) \
#                     else 'The value must be a string.'
#                 raise ValueError(text)
#             print '...func', func
#             func(value, *args, **kwargs)
#         return wrapper
#     if callable(message):
#         return decorator(message)
#     return decorator
#
#
# def string_or_raise(func):
#     def decorator(value, *args, **kwargs):
#         if not isinstance(value, compat.string_type):
#             raise ValueError('Must be a string')
#         return func(value, *args, **kwargs)
#     return decorator
#
#
# def dict_or_raise(message):
#     def decorator(func):
#         @wraps(func)
#         def wrapper(value, *args, **kwargs):
#             if not isinstance(value, dict):
#                 text = message if isinstance(message, compat.string_type) \
#                     else 'The value must be a dictionary.'
#                 raise ValueError(text)
#             func(value, *args, **kwargs)
#         return wrapper
#     if callable(message):
#         return decorator(message)
#     return decorator
#
#
# def list_or_raise(message):
#     def decorator(func):
#         @wraps(func)
#         def wrapper(value, *args, **kwargs):
#             if not isinstance(value, compat.list_type):
#                 text = message if isinstance(message, compat.string_type) \
#                     else 'The value must be a list (, tuple or set).'
#                 raise ValueError(text)
#             func(value, *args, **kwargs)
#         return wrapper
#     if callable(message):
#         return decorator(message)
#     return decorator
#
#
# def try_or_false(method):
#     @wraps(method)
#     def wrapper(self, *args, **kwargs):
#         try:
#             return method(self, *args, **kwargs)
#         except:
#             return False
#     return wrapper
#
#
# def try_or_none(method):
#     @wraps(method)
#     def wrapper(self, *args, **kwargs):
#         try:
#             return method(self, *args, **kwargs)
#         except:
#             return None
#     return wrapper
#
#
# def try_or_dict(method):
#     @wraps(method)
#     def wrapper(self, *args, **kwargs):
#         try:
#             return method(self, *args, **kwargs)
#         except:
#             return {}
#     return wrapper
#
#
# def key_type_or_error(method):
#     @wraps(method)
#     def wrapper(self, key, *args, **kwargs):
#         if not isinstance(key, compat.key_type):
#             raise ValueError('Must be a key type: %s or %s' % compat.key_type)
#         return method(self, key, *args, **kwargs)
#     return wrapper


def value_or_none(func):
    def decorator(value, *args, **kwargs):
        if value is None:
            return None
        return func(value, *args, **kwargs)
    return decorator


def value_or_raise(func):
    def decorator(value, *args, **kwargs):
        if value is None:
            raise ValueError('Must be a object')
        return func(value, *args, **kwargs)
    return decorator


def string_or_none(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, compat.string_type):
            return None
        return func(value, *args, **kwargs)
    return decorator


def string_or_raise(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, compat.string_type):
            raise ValueError('Must be a string')
        return func(value, *args, **kwargs)
    return decorator


def number_or_none(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, compat.int_type):
            return None
        return func(value, *args, **kwargs)
    return decorator


def number_or_raise(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, compat.int_type):
            raise ValueError('Must be a number')
        return func(value, *args, **kwargs)
    return decorator


def int_or_none(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, int):
            return None
        return func(value, *args, **kwargs)
    return decorator


def int_or_raise(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, int):
            raise ValueError('Must be a integer')
        return func(value, *args, **kwargs)
    return decorator


def float_or_none(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, float):
            return None
        return func(value, *args, **kwargs)
    return decorator


def float_or_raise(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, float):
            raise ValueError('Must be a float')
        return func(value, *args, **kwargs)
    return decorator


def list_or_none(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, compat.list_type):
            return None
        return func(value, *args, **kwargs)
    return decorator


def list_or_raise(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, compat.list_type):
            raise ValueError('Must be a list')
        return func(value, *args, **kwargs)
    return decorator


def tuple_or_none(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, tuple):
            return None
        return func(value, *args, **kwargs)
    return decorator


def tuple_or_raise(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, tuple):
            raise ValueError('Must be a tuple')
        return func(value, *args, **kwargs)
    return decorator


def dict_or_none(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, dict):
            return None
        return func(value, *args, **kwargs)
    return decorator


def dict_or_raise(func):
    def decorator(value, *args, **kwargs):
        if not isinstance(value, dict):
            raise ValueError('Must be a dictionary')
        return func(value, *args, **kwargs)
    return decorator


# For Classes

def try_or_none(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except:
            return None
    return wrapper


def try_or_list(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except:
            return []
    return wrapper


def try_or_tuple(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except:
            return ()
    return wrapper


def try_or_dict(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except:
            return {}
    return wrapper


def try_or_false(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except:
            return False
    return wrapper


def key_type_or_error(method):
    @wraps(method)
    def wrapper(self, key, *args, **kwargs):
        if not isinstance(key, compat.key_type):
            raise ValueError('Must be a key type: %s or %s' % compat.key_type)
        return method(self, key, *args, **kwargs)
    return wrapper


# Types

@value_or_none
def _to_bytes(value, encoding=ENCODING, errors='strict'):
    if isinstance(value, compat.text_type):
        value = value.encode(encoding, errors)
    return compat.binary_type(value)


def return_b64(func):
    def decorator(*args, **kwargs):
        value = func(*args, **kwargs)
        return base64.urlsafe_b64encode(_to_bytes(value)).strip(b'=')
    return decorator


def return_sha256(func):
    def decorator(*args, **kwargs):
        value = func(*args, **kwargs)
        return compat.SHA256.new(_to_bytes(value)).hexdigest()
    return decorator


def return_md5(func):
    def decorator(*args, **kwargs):
        value = func(*args, **kwargs)
        return compat.MD5.new(_to_bytes(value)).hexdigest()
    return decorator