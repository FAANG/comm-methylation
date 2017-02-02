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


class OboReader(_AbstractFeatureReader):
    """
    Reader for OBO files.
    """

    def _streaming_iter(self):
        """
        Read next entry from the file (single entry at a time).

        # TODO this can be quadratic since += is used for the obo record
        """
        id = None
        name = ""
        namespace = ""
        parents = []
        for line in self.fp:
            # strip() should also take care of DOS line breaks
            line = line.strip()
            if line=="" :
                if id is not None:
                    yield Entry(**{ 'id' : id, 'name' : name, 'namespace' : namespace, "parents" : parents })
                    id=None
                    parents = []
            else:
                if line.startswith("id: "):
                    id=line.split(": ")[1]
                elif line.startswith("name: "):
                    name=line.split(": ")[1]
                elif line.startswith("namespace: "):
                    namespace=line.split()[1][0].upper()
                elif line.startswith("is_a: "):
                    parents.append(line.split()[1])
                elif line.startswith("relationship: part_of: ") :
                    parents.append(line.split()[3])
                    
        if id is not None:
            yield Entry(**{ 'id' : id, 'name' : name, 'namespace' : namespace, "parents" : parents })

    def _wholefile_iter(self):
        """
        This reads in the entire file at once, but is faster than the above code when there are lots of newlines.
        The idea comes from the TAMO package (http://fraenkel.mit.edu/TAMO/), module TAMO.seq.Fasta (author is
        David Benjamin Gordon).
        """
        wholefile = self.fp.read()
        parts = wholefile.split('\n[Term]')

        id = None
        name = ""
        namespace = ""
        parents = []
        for part in parts:
            
            for line in part.split('\n'):
                line.strip()
                if line.startswith("id: "):
                    id=line.split(": ")[1]
                elif line.startswith("name: "):
                    name=line.split(": ")[1]
                elif line.startswith("namespace: "):
                    namespace=line.split()[1][0].upper()
                elif line.startswith("is_a: "):
                    parents.append(line.split()[1])
                elif line.startswith("relationship: part_of: ") :
                    parents.append(line.split()[3])

            yield Entry(**{ 'id' : id, 'name' : name, 'namespace' : namespace, "parents" : parents })
            parents = []