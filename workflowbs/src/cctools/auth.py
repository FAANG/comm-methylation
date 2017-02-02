# Copyright (c) 2011- The University of Notre Dame.
# This software is distributed under the GNU General Public License.
# See the file COPYING for details.

""" CCTools Authentication module """

from _cctools import auth_register_by_name, auth_register_all

__all__ = ['register', 'register_all']


def register(*names):
    """ Enable specified authentication mode(s). """
    for n in names:
        auth_register_by_name(n)

def register_all():
    """ Enable all authentication modes. """
    auth_register_all()

# vim: set sts=4 sw=4 ts=8 expandtab ft=python:
