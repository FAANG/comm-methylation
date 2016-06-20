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
import sys
import inspect
import logging

from configparser import RawConfigParser, NoOptionError

from jflow.utils import which, display_error_message

class JFlowConfigReader(object):
    """
    """
    
    CONFIG_FILE_PATH = "../../application.properties"
    
    def __init__(self):
        """ 
        """
        self.reader = RawConfigParser()
        self.reader.read(os.path.join(os.path.dirname(inspect.getfile(self.__class__)), self.CONFIG_FILE_PATH))

    def get_tmp_directory(self):
        if not os.path.isdir(self.reader.get("storage", "tmp_directory").replace("$USER",os.getenv("USER"))):
            os.makedirs(self.reader.get("storage", "tmp_directory").replace("$USER",os.getenv("USER")), 0o751)
        return self.reader.get("storage", "tmp_directory").replace("$USER",os.getenv("USER"))
        
    def get_work_directory(self):
        return self.reader.get("storage", "work_directory").replace("$USER",os.getenv("USER"))
    
    def get_exec(self, software):
        try:
            return self.reader.get("softwares", software)
        except NoOptionError:
            return None

    def get_resource(self, resource):
        return self.reader.get("resources", resource)

    def get_log_file_path(self):
        """
        return the log file path
          @return: the path to the log file
        """
        try:
            return self.reader.get('storage', 'log_file').replace("$USER",os.getenv("USER"))
        except :
            raise NoOptionError("Failed when parsing the config file, no section logging found!")
        
    def get_makeflow_path(self):
        try:
            exec_path = self.reader.get("global", "makeflow")
        except NoOptionError:
            exec_path = None
        if exec_path is None: exec_path = "makeflow"
        if which(exec_path) == None:
            logging.getLogger("jflow").exception("'makeflow' path connot be retrieved either in the PATH and in the application.properties file!")
            raise Exception("'makeflow' path connot be retrieved either in the PATH and in the application.properties file!")
        return exec_path

    def get_date_format(self):
        try:
            date_format = self.reader.get("global", "date_format")
        except:
            raise NoOptionError("Failed when parsing the config file, no parameter date_format!")
        return date_format

    def get_batch(self):
        try:
            type = self.reader.get("global", "batch_system_type")
            options = self.reader.get("global", "batch_options")
            limit_submission = self.reader.get("global", "limit_submission")
            return [type, options, limit_submission]
        except NoOptionError:
            return None
          
    def get_socket_options(self):
        try:
            return [self.reader.get("global", "server_socket_host"), int(self.reader.get("global", "server_socket_port"))]
        except:
            return ["127.0.0.1", 8080]
        
    def get_email_options(self):
        try: smtps = self.reader.get("email", "smtp_server")
        except: smtps = None
        try: smtpp = self.reader.get("email", "smtp_port")
        except: smtpp = None
        try: froma = self.reader.get("email", "from_address")
        except: froma = None
        try: fromp = self.reader.get("email", "from_password")
        except: fromp = None
        try: toa = self.reader.get("email", "to_address")
        except: toa = None
        try: subject = self.reader.get("email", "subject")
        except: subject = None
        try: message = self.reader.get("email", "message")
        except: message = None
        return [smtps, smtpp, froma, fromp, toa, subject, message]
    
    def get_component_batch_options(self, component_class):
        try:
            return self.reader.get("components", component_class+".batch_options")
        except:
            return ""
    
    def get_workflow_group(self, workflow_class):
        try:
            return self.reader.get("workflows", workflow_class+".group")
        except:
            return ""
        
         
