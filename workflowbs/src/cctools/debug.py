# Copyright (c) 2011- The University of Notre Dame.
# This software is distributed under the GNU General Public License.
# See the file COPYING for details.

""" CCTools Debugging module """

__all__ = ['set_name', 'set_file', 'set_flag', 'print_flags', 'clear_flags']

from _cctools import debug_config, debug_config_file, debug_config_file_size
from _cctools import debug_flags_set, debug_flags_clear, debug_flags_print

import sys


def set_name(name=None):
    """ Set name of program to debug. """
    if name is None:
        name = sys.argv[0]
    debug_config(name)

def set_file(path=None, size=None):
    """ Direct debug output to a file. """
    if path:
        debug_config_file(path)
    if size:
        debug_config_file_size(size)

def set_flags(*flags):
    """ Enable specified debugging flags. """
    for f in flags:
        debug_flags_set(f)

def clear_flags():
    """ Clear all debugging flags. """
    debug_flags_clear()

def print_flags(stream=None):
    """ Print available debugging flags. """
    if stream is None:
        stream = sys.stdout

    debug_flags_print(stream)
    stream.write('\n')

# vim: set sts=4 sw=4 ts=8 expandtab ft=python:
