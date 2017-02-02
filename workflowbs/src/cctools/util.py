# Copyright (c) 2011- The University of Notre Dame.
# This software is distributed under the GNU General Public License.
# See the file COPYING for details.

""" CCTools Utility module """



from cctools.compat import map

import functools
import sys

__all__ = ['catch_exception', 'dump', 'time_format', 'iterable', 'type_str']


def catch_exception(error, default=None):
    def wrapper(f):
        @functools.wraps(f)
        def decorator(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except error:
                return default
        return decorator
    return wrapper


def dump(expr, stream=sys.stdout):
    """ Print expression and its value. """
    frame = sys._getframe(1)
    locals = frame.f_locals
    globals = frame.f_globals
    value = eval(expr, globals, locals)

    if isinstance(value, str):
        print(expr + ' = ' + value, file=stream)
    elif iterable(value):
        print(expr + ' = ' + ', '.join(map(str, value)), file=stream)
    else:
        print(expr + ' = ' + str(value), file=stream)


def time_format(seconds):
    """ Return `seconds` formatted as string year:day:hour:minute:second. """
    TDELTAS = (60, 60, 24, 365, 10)
    tlist   = []
    ctime   = seconds

    if seconds is None:
        return None

    for d in TDELTAS:
        if ctime >= d:
            tlist.append(ctime % d)
            ctime = ctime / d
        else:
            tlist.append(ctime)
            break

    return ':'.join(reversed(['%02d' % t for t in tlist]))


def iterable(obj):
    """ Return whether or not an item is iterable. """
    return hasattr(obj, '__iter__')


def type_str(obj, full=False):
    """ Return string representation of object's type. """
    if obj.__class__ == type:
        obj_type = repr(obj)
    else:
        obj_type = str(obj.__class__)

    if full:
        return obj_type.split("'")[1]
    else:
        return obj_type.split("'")[1].split(".")[-1]


def split_pair(s, divider):
    i = s.index(divider)
    return s[0:i], s[i+len(divider):]

# vim: set sts=4 sw=4 ts=8 expandtab ft=python:
