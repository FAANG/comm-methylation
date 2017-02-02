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


class BEDReader(_AbstractFeatureReader):
    '''
        Reader for BED
    '''
    def _process_line(self,line):
        row = line.rstrip().split('\t')
        if len(row) not in list(range(3,13)) : raise FormatError('Invalid number of columns in your BED file {0}'.format( len(row)))
        return Entry(**{ 'chrom' : row[0], 'chromStart' : row[1], 'chromEnd' : row[2] })
        
    def _streaming_iter(self):
        for line in self.fp :
            if line.startswith('#') :
                continue
            yield self._process_line(line)
    
    def _wholefile_iter(self):
        wholefile = self.fp.read()
        assert len(wholefile) != 0 , "Empty BED file"
        
        for line in wholefile.split('\n') :
            if line.startswith('#') :
                continue
            yield self._process_line(line)