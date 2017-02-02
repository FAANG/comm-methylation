# Copyright (c) 2011- The University of Notre Dame.
# This software is distributed under the GNU General Public License.
# See the file COPYING for details.

""" CCTools Error module """

from cctools.util import type_str

import functools

__all__ = ['CCToolsError', 'ParserError', 'raise_parser_error']


class CCToolsError(Exception):
    """
    This is the base custom :class:`Exception` used throughout the library.
    """

    def __init__(self, system, message):
        Exception.__init__(self)
        if isinstance(system, str):
            self.system = system
        else:
            self.system = type_str(system)
        self.message = message

    def __str__(self):
        return '{0}: {1}'.format(self.system, self.message)


class ParserError(CCToolsError):
    """ This is the error class used by various parsers. """

    def __init__(self, system, token, line=None):
        if line:
            message = 'unable to parse "{0}" in line: "{1}"'.format(token, line)
        else:
            message = 'unable to parse: {0}'.format(token)
        CCToolsError.__init__(self, system, message)


def raise_parser_error(error, token, parser_error=ParserError):
    """ This decorator raises a ParserError if parsing a line fails. """
    def wrapper(f):
        @functools.wraps(f)
        def decorator(self, line):
            try:
                f(self, line)
            except error:
                raise parser_error(self, token.upper(), line)
        return decorator
    return wrapper

# vim: set sts=4 sw=4 ts=8 expandtab ft=python:
