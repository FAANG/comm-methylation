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

from jflow.seqio import FormatError
from jflow.seqio import UnknownFileType

from .abstractfeaturereader import _AbstractFeatureReader, Entry, boolify, autocast


class WEGOReader(_AbstractFeatureReader):
    '''
        Reader for WEGO files
    '''
    
    def _process_line(self,line):
        row = line.rstrip().split('\t')
        name, ids = row[0], []
        if len(row) > 1 :
            ids = row[1:]
        return (name, ids)  
        
    def _streaming_iter(self):
        
        # first line must be !WGOP
        if not self.fp.readline().startswith('!WGOP'):
            raise FormatError('WEGO header not found (!WEGOP_), invalid WEGO file ')
        
        for line in fp :
            if line.startswith('!WEGO') :
                continue
            yield self._process_line(line)  
    
    def _wholefile_iter(self):
        wholefile = self.fp.read()
        assert len(wholefile) != 0 , "Empty WEGO file"
        if not wholefile.startswith('!WGOP') :
            raise FormatError('WEGO header not found (!WEGOP_), invalid WEGO file ')
        
        for line in wholefile.split('\n') :
            if line.startswith('!WEGO') :
                continue
            yield self._process_line(line)