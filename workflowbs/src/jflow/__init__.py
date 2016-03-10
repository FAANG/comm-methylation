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

__version__ = '1.0'

import logging
import os

from jflow.config_reader import JFlowConfigReader

# Define some Error classes
class InvalidFormatError(Exception): pass

jflowconf = JFlowConfigReader()

# if log file directory does not exist, create it
log_directory = os.path.dirname(jflowconf.get_log_file_path())
if not os.path.isdir(log_directory):
    os.makedirs(log_directory, 0o751)
    
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=jflowconf.get_log_file_path(),
                    filemode='a')