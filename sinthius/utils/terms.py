#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ~
# Author: Alejandro M. Bernardis
# Email: alejandro.bernardis@gmail.com
# Created: 10/Jun/2016 22:28
# ~

from pygments import highlight
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexers.javascript import JavascriptLexer
from sinthius import compat
from sinthius.utils.decorators import value_or_none

RESET = '0'

opt_dict = {'bold': '1', 'underscore': '4', 'blink': '5', 'reverse': '7',
            'conceal': '8'}

color_names = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan',
               'white')

foreground = {color_names[x]: '3%s' % x for x in range(8)}
background = {color_names[x]: '4%s' % x for x in range(8)}


@value_or_none
def colorize(text='', opts=(), **kwargs):
    """
    Returns your text, enclosed in ANSI graphics codes.

    Depends on the keyword arguments 'fg' and 'bg', and the contents of
    the opts tuple/list.

    Returns the RESET code if no parameters are given.

    Valid colors:
        'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'

    Valid options:
        'bold'
        'underscore'
        'blink'
        'reverse'
        'conceal'
        'noreset' - string will not be auto-terminated with the RESET code

    Examples:
        colorize('hello', fg='red', bg='blue', opts=('blink',))
        colorize()
        colorize('goodbye', opts=('underscore',))
        print(colorize('first line', fg='red', opts=('noreset',)))
        print('this should be red too')
        print(colorize('and so should this'))
        print('this should not be red')
    """
    code_list = []
    if text == '' and len(opts) == 1 and opts[0] == 'reset':
        return '\x1b[%sm' % RESET
    for k, v in compat.iteritems(kwargs):
        if k == 'fg':
            code_list.append(foreground[v])
        elif k == 'bg':
            code_list.append(background[v])
    for o in opts:
        if o in opt_dict:
            code_list.append(opt_dict[o])
    if 'noreset' not in opts:
        text = '%s\x1b[%sm' % (text or '', RESET)
    return '%s%s' % (('\x1b[%sm' % ';'.join(code_list)), text or '')


def make_style(opts=(), **kwargs):
    return lambda text: colorize(text, opts, **kwargs)


@value_or_none
def jsoncolorize(value):
    return highlight(value, JavascriptLexer(), TerminalFormatter())
