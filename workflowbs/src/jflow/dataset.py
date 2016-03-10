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

from weaver.dataset import *

class ArrayList(Dataset):
    """ This :class:`Dataset` consists of file paths specified by an ``Array``
    expression.
    """
    def __init__(self, array):
        Dataset.__init__(self)
        self.array = array

    @cache_generation
    def _generate(self):
        return (MakeFile(normalize_path(f.strip(), os.curdir), self.nest)
                for f in self.array)