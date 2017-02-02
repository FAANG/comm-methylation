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

import sys, os

# First found out workflows module
path = os.path.abspath(sys.argv[0])
while os.path.dirname(path) != path:
    if os.path.exists(os.path.join(path, 'workflows', '__init__.py')):
        sys.path.insert(0, path)
        break
    path = os.path.dirname(path)

# Then found out sources module
path = os.path.abspath(sys.argv[0])
while os.path.dirname(path) != path:
    if os.path.exists(os.path.join(path, 'jflow', '__init__.py')):
        sys.path.insert(0, path)
        break
    elif os.path.exists(os.path.join(path, 'src', 'jflow', '__init__.py')):
        sys.path.insert(0, os.path.join(path, 'src'))
        break
    path = os.path.dirname(path)