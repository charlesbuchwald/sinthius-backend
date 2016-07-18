#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:27
# ~

import copy


def make_optional(property_dict, test_key):
    for key, value in property_dict.iteritems():
        if test_key(key):
            property_dict[key]['required'] = False
    return property_dict


def copy_properties(target_dict, source_dict):
    for key, value in source_dict['properties'].iteritems():
        if key in target_dict['properties']:
            raise KeyError('Key "%s" can\'t be in properties' % key)
        if target_dict['properties'][key] != value:
            raise ValueError('Key(%s) Value(%s) is not equal to "%s".'
                             % (key, value, target_dict['properties'][key]))
        target_dict['properties'][key] = copy.deepcopy(value)
