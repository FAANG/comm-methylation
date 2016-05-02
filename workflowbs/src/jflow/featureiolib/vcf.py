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

from .abstractfeaturereader import _AbstractFeatureReader, Entry, boolify, autocast


class VCFReader(_AbstractFeatureReader):
    '''
        Reader for VCF files
        Read a vcf file and yield an entry object. Each line will be yield as an Entry object. To access samples for 
        variation, use entry.samples, which will be an array of Entry
        
        Fields for a variation entry :
            entry.chrom, entry.pos, entry.id, entry.ref, entry.alt, entry.qual, entry.filter, entry.info, entry.format
            entry.is_indel
            special case :
                * entry.alt     : array of string
                * entry.info    : dictionary
                * entry.samples : array of entries
            
        Fields of a sample entry :
            entry.name, entry.path
            all other fields depends on the FORMAT column
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
        self.samples_name=[]
        self._init_sample_names()

    def _init_sample_names(self):
        for line in self.fp :
            if line.startswith('#') :
                if line.startswith('#CHROM') :
                    row = line.rstrip().split('\t')
                    if len(row) < 8 : 
                        raise FormatError( 'Invalid number of columns in your vcf header file {0}'.format(len(row)) )
                    for i in range(9, len(row)) :
                        self.samples_name.append( ( row[i] , os.path.splitext(os.path.basename(row[i]))[0]  ) )
                    break
            else :
                raise FormatError( 'The vcf file {0}must start with header lines (#) !!!'.format(self.fp.name) )
        self.fp.seek(0,0)
        #if len(self.samples_name) < 0 :
        #    raise FormatError(  "Invalid VCF file {0}. Could not retrieve the sample names headers".format(self.fp.name) )
    
    def _process_line(self,line):
        row = line.rstrip().split('\t')
        variation = Entry(**{ 
           'chrom'   : row [0], 
           'pos'     : int(row[1]), 
           'id'      : row[2], 
           'ref'     : row[3], 
           'alt'     : row[4].split(',') , 
           'qual'    : autocast(row[5]),
           'filter'  : row[6],
           'info'    : {},
           'format'  : [],
           'samples' : [],
           'is_indel': False
          })
        
        if len(variation.alt) > 1 :
            variation.addattr( 'is_indel', True)
        
        regexp_none=re.compile("\.(\/\.)*")
        
        if len(row) == 8 and row[7] != '.' :
            info={}
            for p in row[7].split(';') :
                tab= p.split('=')
                if len(tab)>1 :
                    info[tab[0]] = autocast(tab[1])
                else :
                    info[tab[0]] = True
            variation.addattr( 'info', info)
        if len(row) > 8 :  
            format = row[8].split(':')
            variation.format = format
            for lib_infos in range (9,len(row)) :
                if not regexp_none.match(row[lib_infos]):
                    sformat = row[lib_infos].split(':')
                    variation.samples.append( Entry(**{ autocast(format[i]) : autocast(sformat[i]) if sformat[i] != '.' else None for i in range(0,len(format)) } )  )
                else :
                    variation.samples.append( Entry(**{ autocast(format[i]) : None for i in range(0,len(format)) }) )
        return variation
    
    def _streaming_iter(self):
        for line in self.fp :
            if line.startswith('#') :
                continue
            yield self._process_line(line)
    
    def _wholefile_iter(self):
        wholefile = self.fp.read()
        assert len(wholefile) != 0 , "Empty VCF file"
        for line in wholefile.split('\n') :
            if line.startswith('#') :
                continue
            yield self._process_line(line) 