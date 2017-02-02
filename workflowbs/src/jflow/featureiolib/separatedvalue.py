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


class SeparatedValueIO(object):
    """
     @summary : Specific handler for separated value file (examples : TSV, CSV).
    """
    def __init__(self, file_path, separator="\t", mode="r"):
        """
        @param file_path : [str] The filepath.
        @param separator : [str] The value separator.
        @param mode : [str] Mode to open the file ('r', 'w', 'a').
        """
        self._path = file_path
        self._handle = open( file_path, mode )
        self._line = 1
        self._separator = separator

    def __del__(self):
        self.close()

    def close(self):
        if  hasattr(self, '_handle') and self._handle is not None:
            self._handle.close()
            self._handle = None
            self._line = None

    def __iter__(self):
        for line in self._handle:
            line = line.rstrip('\n')
            self._line += 1
            try:
                record = line.split(self._separator)
            except:
                raise IOError( "The line " + str(self._line) + " in '" + self._path + "' cannot be parsed by " + self.__class__.__name__ + 
                               " with separator '" + self._separator + "'.\n" + "Line content : " + line )
            else:
                yield record

    def __next__(self):
        """
         @summary : Returns the next line record.
         @return : [list] The line record.
        """
        line = self._handle.readline()
        self._line += 1
        try:
            record = line.split(self._separator)
        except:
            raise IOError( "The line " + str(self._line) + " in '" + self._path + "' cannot be parsed by " + self.__class__.__name__ + 
                           " with separator '" + self._separator + "'.\n" + "Line content : " + line )

    def write(self, record):
        """
         @summary : Write one line on SparatedValue file.
          @param record : [list] the list to write.
        """
        self._handle.write( record.join(self._separator) + "\n" )
        self._line += 1