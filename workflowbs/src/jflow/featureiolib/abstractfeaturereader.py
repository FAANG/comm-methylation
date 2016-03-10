#
# Copyright (C) 2015 INRA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import re

from jflow.seqio import xopen
from jflow.seqio import FormatError
from jflow.seqio import UnknownFileType


def boolify(s):
    return {'True': True, 'False': False}[s]

def autocast(s):
    for fn in (boolify, int, float):
        try:
            return fn(s)
        except:
            pass
    return s

class Entry(object):
    def __init__(self, **kwargs):
        self.attrib = kwargs
    
    def addattr(self, k, v):
        self.attrib[k] = v
        
    def __getattr__(self, key):
        return self.attrib[key]
    
    def __str__(self):
        return str(self.attrib)

    def __getitem__(self, key):
        return self.attrib[key]

    def has(self,attr):
        return attr in self.attrib
        
class _AbstractFeatureReader(object):
    '''
        Abstract file reader
    '''
    def __init__(self, file, wholefile=False):
        """
            @param file : filename or a file-like object. 
            @param wholefile: If True, then it is ok to read the entire file  into memory. This is faster when there are 
                many newlines in the file, but may obviously need a lot of memory.
        """
        if isinstance(file, str):
            file = xopen(file, "r")
        self.fp = file
        self.wholefile = wholefile
    
    def __iter__(self):
        return self._wholefile_iter() if self.wholefile else self._streaming_iter()
    
    def _streaming_iter(self):
        raise NotImplementedError('not implemented')

    def _wholefile_iter(self):
        raise NotImplementedError('not implemented')
    
    def __enter__(self):
        if self.fp is None:
            raise ValueError("I/O operation on closed {0}".format(self.__class__.__name__) )
        return self

    def __exit__(self, *args):
        self.fp.close()