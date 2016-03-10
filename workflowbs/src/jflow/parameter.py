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

import re
import sys
import types
import datetime
import logging
import argparse
import os
import fnmatch
import tempfile
import urllib.parse
import random

from argparse import _ensure_value
from urllib.request import urlopen
import copy as _copy
from urllib.parse import urlparse
import pickle

from jflow.config_reader import JFlowConfigReader
from jflow.utils import get_octet_string_representation, get_nb_octet, display_error_message

# import custom types and custom formats
from workflows.types import *
from workflows.formats import *
import collections


# define all input type available
INPUTFILE_TYPES = ["inputfile", "localfile", "urlfile", "browsefile"]
INPUTFILES_TYPES = ["inputfiles", "localfile", "urlfile", "browsefile", "regexpfiles"]

def inputdirectory(directory):
    if os.path.isdir(directory):
        return directory
    else:
        raise argparse.ArgumentTypeError("'" + directory + "' is not a valid directory!")

def browsefile(file):
    # browsefile are not available from command line, considere it as a localfile
    # from the gui, this will not been tested this way
    return localfile(file)

def localfile(file):
    if os.path.isfile(file):
        return file
    else:
        raise argparse.ArgumentTypeError("'" + file + "' is not a valid file!")

def urlfile(file):
    uri_object = urlparse(file)
    try:
        opener = urlopen(file)
    except:
        raise argparse.ArgumentTypeError("URL '" + file + "' is invalid!")
    file_name = os.path.basename(uri_object.path)
    if file_name is not None and file_name != "":
        metadata = opener.info()
        file_size = int(metadata.getheaders("Content-Length")[0])
        if file_size == 0:
            raise argparse.ArgumentTypeError("The URL file '" + file + "' is empty!")
        return file
    else:
        raise argparse.ArgumentTypeError("URL '" + file + "' does not contain any file name!")

def inputfile(file):
    # test the format
    uri_object = urlparse(file)
    # check the file
    if uri_object.scheme == '':
        return localfile(file)
    else:
        return urlfile(file)

def inputfiles(file):
    # test the format
    uri_object = urlparse(file)
    # check the file
    if uri_object.scheme == '':
        try:
            regexpfiles(file)
            return file
        except:
            return localfile(file)
    else:
        return urlfile(file)

def regexpfiles(files_pattern):
    try:
        if ':' in files_pattern:
            folder, pattern = files_pattern.rsplit(':')
        else:
            folder, pattern = os.path.split(files_pattern)
    except:
        raise argparse.ArgumentTypeError("Regexp '" + files_pattern + "' is invalid!")
    if not pattern:
        raise argparse.ArgumentTypeError("Regexp '" + files_pattern + "' is invalid!")
    if not os.path.exists(folder):
        raise argparse.ArgumentTypeError("The folder '" + folder + "' doesn't exist!")
    if not os.access(folder, os.R_OK):
        raise argparse.ArgumentTypeError("You do not have permission to read '" + folder + "'!")
    nb_files = 0
    for item in sorted(os.listdir(folder)):
        if os.path.isfile(os.path.join(folder, item)) and fnmatch.fnmatch(item, pattern):
            nb_files += 1
    if nb_files == 0:
        raise argparse.ArgumentTypeError("0 file selected by the regexp!")
    return files_pattern

def password(pwd):
    return PasswordParameter.encrypt(pwd)

def create_test_function(itype):
    try:
        ctype, csizel = itype.split(AbstractInputFile.SIZE_LIMIT_SPLITER)    
        def inner_function(ifile):
            # first eval the asked type
            returned_value = eval(ctype)(ifile)
            # if 0 unlimited size
            if csizel != "0":
                # first test the size of the file
                uri_object = urlparse(ifile)
                if uri_object.scheme == '':
                    isize = 0
                    try:
                        regexpfiles(ifile)
                        if ':' in returned_value:
                            folder, pattern = returned_value.rsplit(':')
                        else:
                            folder, pattern = os.path.split(returned_value)
                        for item in os.listdir(folder):
                            if os.path.isfile(os.path.join(folder, item)) and fnmatch.fnmatch(item, pattern):
                                isize += os.path.getsize(os.path.abspath(os.path.join(folder, item)))
                    except:
                        isize = os.path.getsize(ifile)
                    if isize > int(get_nb_octet(csizel)):
                        raise argparse.ArgumentTypeError("File '" + ifile + "' (size=" + get_octet_string_representation(isize) + ") exceeds size limits: " + csizel + ".")
                else:
                    try:
                        opener = urlopen(ifile)
                        metadata = opener.info()
                        isize = int(metadata.getheaders("Content-Length")[0])
                        if isize > int(get_nb_octet(csizel)):
                            raise argparse.ArgumentTypeError("File '" + ifile + "' (size=" + get_octet_string_representation(isize) + ") exceeds size limits: " + csizel + ".")
                    except:
                        raise argparse.ArgumentTypeError("URL '" + file + "' is invalid!")
            # then test the type
            return returned_value
        
        inner_function.__name__ = ctype+AbstractInputFile.SIZE_LIMIT_SPLITER+csizel
        return inner_function
    except:
        if type(itype) == str:
            return eval(itype)
        else:
            return itype

class MultipleParameters(object):
    def __init__(self, types, required, choices, excludes, default, actions):
        self.types = types
        self.choices = choices
        self.excludes = excludes
        self.default = default
        self.actions = actions
        self.index = None
        self.required = required
        self.__name__ = "MultipleParameters"

    def get_help(self):
        help = " ("
        for flag in list(self.types.keys()):
            help += flag + "=<" + self.types[flag].__name__.upper() + ">, "
        return help[:-2] + ")"

    def __call__(self, arg):
        parts = arg.split("=")
        if not parts[0] in self.types:
            raise argparse.ArgumentTypeError(parts[0] + " is an invalid flag! Available ones are: "+", ".join(list(self.types.keys())))

        if self.types[parts[0]] == bool:
            return (parts[0], not self.default[parts[0]], self.required, self.excludes)
        else:
            try:
                value = self.types[parts[0]](parts[1])
            except:
                raise argparse.ArgumentTypeError("invalid " + self.types[parts[0]].__name__ + " value: '" + parts[1] + "' for sub parameter '" + parts[0] + "'")
            
            if self.choices[parts[0]] != None:
                if value not in self.choices[parts[0]]:
                    raise argparse.ArgumentTypeError("argument " + parts[0] + ": invalid choice: '" + parts[1] + "' (choose from " + ", ".join(map(str,self.choices[parts[0]])) + ")")

            self.index = parts[0]
            return (parts[0], value, self.required, self.excludes, self.actions)

class MiltipleAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # what is commun within required and excludes
        exclusif_required = {}
        for exclude_group in values[0][3]:
            exclusif_required[exclude_group] = False
            for param in values[0][3][exclude_group]:
                if param in values[0][2]:
                    exclusif_required[exclude_group] = True
        given_params = []
        # first check for required parameters
        try:
            required = _copy.copy(values[0][2])
            # delete required that are exclusive
            for group in exclusif_required:
                if exclusif_required[group]:
                    for val in values[0][3][group]:
                        if val in required:
                            del required[required.index(val)]
            for val in values:
                given_params.append(val[0])
                if val[0] in required:
                    del required[required.index(val[0])]
        except: pass
        if len(required) == 1: parser.error(", ".join(required) + " is a required parameter!")
        elif len(required) > 1: parser.error(", ".join(required) + " are required parameters!")
        # then for exclude ones    
        for exclude_group in values[0][3]:
            found = None
            for param in values[0][3][exclude_group]:
                if param in given_params and found != None:
                    parser.error("argument '" + found + "': not allowed with argument '" + param + "'")
                    break
                elif param in given_params: found = param

        # check for required exclusive if one of them is in
        if len(list(exclusif_required.keys())) > 0:
            for group in exclusif_required:
                if exclusif_required[group]:
                    rfound = False
                    for param in values[0][3][group]:
                        if param in given_params: rfound = True
            if not rfound: parser.error("one of the arguments: " + ", ".join(values[0][3][group]) + " is required")

        # if ok add the value
        final_hash, final_values = {}, []
        for value in values:
            if values[0][4][value[0]] == "append" and value[0] in final_hash:
                final_hash[value[0]].append(value[1])
            elif values[0][4][value[0]] == "append":
                final_hash[value[0]]= [value[1]]
            else:
                final_hash[value[0]]= value[1]
        for param in final_hash:
            final_values.append((param, final_hash[param]))
        setattr(namespace, self.dest, final_values)


class MiltipleAppendAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # what is commun within required and excludes
        exclusif_required = {}
        for exclude_group in values[0][3]:
            exclusif_required[exclude_group] = False
            for param in values[0][3][exclude_group]:
                if param in values[0][2]:
                    exclusif_required[exclude_group] = True
        given_params = []
        # first check for required parameters
        try:
            required = _copy.copy(values[0][2])
            # delete required that are exclusive
            for group in exclusif_required:
                if exclusif_required[group]:
                    for val in values[0][3][group]:
                        if val in required:
                            del required[required.index(val)]
            for val in values:
                given_params.append(val[0])
                if val[0] in required:
                    del required[required.index(val[0])]
        except: pass
        if len(required) == 1: parser.error(", ".join(required) + " is a required parameter!")
        elif len(required) > 1: parser.error(", ".join(required) + " are required parameters!")
        # then for exclude ones    
        for exclude_group in values[0][3]:
            found = None
            for param in values[0][3][exclude_group]:
                if param in given_params and found != None:
                    parser.error("argument '" + found + "': not allowed with argument '" + param + "'")
                    break
                elif param in given_params: found = param

        # check for required exclusive if one of them is in
        if len(list(exclusif_required.keys())) > 0:
            for group in exclusif_required:
                if exclusif_required[group]:
                    rfound = False
                    for param in values[0][3][group]:
                        if param in given_params: rfound = True
            if not rfound: parser.error("one of the arguments: " + ", ".join(values[0][3][group]) + " is required")
        # if ok add the value
        items = _copy.copy(_ensure_value(namespace, self.dest, []))
        final_hash, final_values = {}, []
        for value in values:
            if values[0][4][value[0]] == "append" and value[0] in final_hash:
                final_hash[value[0]].append(value[1])
            elif values[0][4][value[0]] == "append":
                final_hash[value[0]]= [value[1]]
            else:
                final_hash[value[0]]= value[1]
        for param in final_hash:
            final_values.append((param, final_hash[param]))
        items.append(final_values)
        setattr(namespace, self.dest, items)


class AbstractParameter(object):

    def __init__(self, name, help, default=None, type=str, choices=None, required=False,
                 flag=None, action="store", sub_parameters=None, group="default", display_name=None, 
                 cmd_format="", argpos=-1):

        self.name = name
        self.help = help
        self.action = action
        self.nargs = None
        if sub_parameters:
            self.sub_parameters = sub_parameters
        else: self.sub_parameters = []
        self.group = group
        if flag == None:
            self.flag = "--"+name.replace("_", "-")
        else: self.flag = flag
        if display_name == None:
            self.display_name = name.replace("_", " ").title()
        else: self.display_name = display_name
        self.required = required
        self.choices = choices
        self.argpos = argpos
        self.cmd_format = cmd_format
        
        # Set parameter type
        if type == "date":
            self.type = date
        elif type == "multiple":
            self.type = "multiple"
        elif isinstance(type, types.FunctionType):
            self.type = type
        elif type in [str, int, float, bool]:
            self.type = type
        else:
            try: self.type = eval(type)
            except: self.type = str

        # Set parameter value
        if choices != None and default == None:
            self.default = choices[0]
        else:
            self.default = default

    def export_to_argparse(self):
        if self.type == bool and str(self.default).lower() in (False, "false",  "f", "0"):
            return {"help": self.help, "required": self.required, "dest": self.name, 
                    "default": False, "action": "store_true"}
        elif self.type == bool:
            return {"help": self.help, "required": self.required, "dest": self.name, 
                    "default": True, "action": "store_false"}
        elif self.nargs != None:
            return {"type": self.get_test_function(), "help": self.help, "required": self.required,
                    "dest": self.name, "default": self.default,
                    "action": self.action, "choices": self.choices, "nargs": self.nargs}
        else:
            return {"type": self.get_test_function(), "help": self.help, "required": self.required,
                    "dest": self.name, "default": self.default,
                    "action": self.action, "choices": self.choices}

    def get_type(self):
        return self.type.__name__

    def get_test_function(self):
        return create_test_function(self.type)


class LinkTraceback(object):

    def __init__(self, linkTrace_nameid=None, parent_linkTrace_nameid=None):
        self.linkTrace_nameid = linkTrace_nameid
        self.parent_linkTrace_nameid = [] if parent_linkTrace_nameid == None else parent_linkTrace_nameid

class AbstractIOFile(LinkTraceback):

    def __init__(self, file_format="any", linkTrace_nameid=None, parent_linkTrace_nameid=None):
        LinkTraceback.__init__(self, linkTrace_nameid, parent_linkTrace_nameid)
        self.file_format = file_format


class IOFile(str, AbstractIOFile):

    def __new__(self, val="", file_format="any", linkTrace_nameid=None, parent_linkTrace_nameid=None):
        return str.__new__(self, val)

    def __init__(self, val="", file_format="any", linkTrace_nameid=None, parent_linkTrace_nameid=None):
        AbstractIOFile.__init__(self, file_format, linkTrace_nameid, parent_linkTrace_nameid)

    def __getnewargs__(self):
        return (str(self), self.file_format, self.linkTrace_nameid, self.parent_linkTrace_nameid)
        

class MultiParameter(dict, AbstractParameter):

    def __init__(self, name, help, required=False, flag=None, group="default", display_name=None, cmd_format="", argpos=-1):
        AbstractParameter.__init__(self, name, help, required=required, type="multiple", flag=flag, group=group, 
                                   display_name=display_name, cmd_format=cmd_format, argpos=argpos)
        return dict.__init__(self, {})

    def add_sub_parameter(self, param):
        param_flag = param.flag[2:]
        if self.type == "multiple":
            if param.required: req = [param_flag] 
            else: req = []
            self.type = MultipleParameters({param_flag: param.type}, req, 
                                           {param_flag: param.choices}, {}, {param_flag: param.default},
                                           {param_flag: param.action})
            if self.action == "append":
                self.action = MiltipleAppendAction
            else:
                self.action = MiltipleAction
            self.global_help = self.help
            self.help = self.global_help + " (" + param_flag + "=<" + param.type.__name__.upper() + ">)"
            self.default = {}
            self.nargs = "+"
        elif self.type.__class__ == MultipleParameters:
            self.type.types[param_flag] = param.type
            self.type.choices[param_flag] = param.choices
            self.type.default[param_flag] = param.default if param != None else None
            self.type.actions[param_flag] = param.action
            if param.required:
                self.type.required.append(param_flag)
            self.help = self.global_help + self.type.get_help()
        param.flag = param_flag
        self.sub_parameters.append(param)
        
        
class MultiParameterList(list, AbstractParameter):

    def __init__(self, name, help, required=False, flag=None, group="default", display_name=None, cmd_format="", argpos=-1):
        AbstractParameter.__init__(self, name, help, required=required, type="multiple", flag=flag, 
                                   action="append", group=group, display_name=display_name, 
                                   cmd_format=cmd_format, argpos=argpos)
        return list.__init__(self, [])

    def add_sub_parameter(self, param):
        param_flag = param.flag[2:]
        if self.type == "multiple":
            if param.required: req = [param_flag]
            else: req = []
            self.type = MultipleParameters({param_flag: param.type}, req,
                                           {param_flag: param.choices}, {}, {param_flag: param.default},
                                           {param_flag: param.action})
            if self.action == "append":
                self.action = MiltipleAppendAction
            else:
                self.action = MiltipleAction
            self.global_help = self.help
            self.help = self.global_help + " (" + param_flag + "=<" + param.type.__name__.upper() + ">)"
            self.default = []
            self.nargs = "+"
        elif self.type.__class__ == MultipleParameters:
            self.type.types[param_flag] = param.type
            self.type.choices[param_flag] = param.choices
            self.type.default[param_flag] = param.default if param != None else None
            self.type.actions[param_flag] = param.action
            if param.required:
                self.type.required.append(param_flag)
            self.help = self.global_help + self.type.get_help()
        param.flag = param_flag
        self.sub_parameters.append(param)
    
    def __getitem__(self, key):
            getitem = self.__dict__.get("__getitem__", list.__getitem__)
            if isinstance(key, int):
                return getitem(self, key)
            else :
                if len(self) > 0:
                    if key in getitem(self, 0):
                        res=[]
                        for mparam in self :
                            if isinstance(getitem(self, 0)[key], list):
                                res.extend(mparam[key])
                            else:
                                res.append(mparam[key])
                        return res
                else:
                        return []

class ParameterFactory(object):
    @staticmethod
    def factory(*args, **kwargs):
        if not "type" in kwargs:
            return StrParameter( *args, **kwargs )

        if kwargs["type"] == "int" or kwargs["type"] is int:
            return IntParameter( *args, **kwargs )
        elif kwargs["type"] == "bool" or kwargs["type"] is bool:
            return BoolParameter( *args, **kwargs )
        elif kwargs["type"] == "float" or kwargs["type"] is float:
            return FloatParameter( *args, **kwargs )
        elif kwargs["type"] == "date" or kwargs["type"] == date:
            return DateParameter( *args, **kwargs )
        elif kwargs["type"] == "password" or kwargs["type"] == password:
            return PasswordParameter( *args, **kwargs )
        else:
            return StrParameter( *args, **kwargs )


def none_decorator(fn):
    
    def new_func(*args, **kwargs):
        if args[0].is_None:
            print (fn)
            raise Exception("The parameter '" + args[0].name + "' is None.")
        else:
            return fn(*args, **kwargs)
    return new_func


class BoolParameter(int, AbstractParameter):

    def __new__(self, name, help, default=False, type=bool, choices=None, required=False,
                flag=None, sub_parameters=None, group="default", display_name=None,  cmd_format="", argpos=-1):
        
        bool_default = True
        if default == None or default in [False, 0]:
            bool_default = False
        elif default.__class__.__name__ == "str" and default in ["False", "F", "false", "f", 0, "0"]:
            bool_default = False
            
        val = int.__new__(self, bool_default)
        val.is_None = False if default != None else True
        for attr in bool.__dict__:
            func = getattr(bool, attr)
            if isinstance(func, collections.Callable) and attr not in ["__new__", "__init__", "__getattribute__", "__setattribute__",
                                               "__eq__", "__ne__", "__bool__", "__str__", "__repr__", "__getnewargs__"]:
                setattr(BoolParameter, attr, none_decorator(func))
        return val

    def __init__(self, name, help, default=None, type=bool, choices=None, required=False,
                 flag=None, sub_parameters=None, group="default", display_name=None, cmd_format="", argpos=-1):
        AbstractParameter.__init__(self, name, help, flag=flag, default=bool(default), type=type, choices=choices, required=required, 
                                   action="store", sub_parameters=sub_parameters, group=group, display_name=display_name,  cmd_format=cmd_format, argpos=argpos)

    def __getnewargs__(self):
        return (self.name, self.help, self.default, self.type, self.choices, self.required, self.flag,
                self.sub_parameters, self.group, self.display_name, self.cmd_format, self.argpos)

    def __str__(self):
        if self.is_None:
            return str(None)
        return str(bool(self))

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if other.__class__.__name__ == "NoneType":
            return self.is_None
        elif self.is_None:
            return False
        else:
            return int(self) == int(bool(other))

    def __ne__(self, other):
        return not (self == other)

    def __bool__(self):
        if self.is_None:
            return False
        else:
            return self != 0


class IntParameter(int, AbstractParameter):

    def __new__(self, name, help, default=None, type=int, choices=None, required=False,
                flag=None, sub_parameters=None, group="default", display_name=None,  cmd_format="", argpos=-1):
        int_default = 0 if default == None else int(default)
        val = int.__new__(self, int_default)
        val.is_None = False if default != None else True
        for attr in int.__dict__:
            func = getattr(int, attr)
            if isinstance(func, collections.Callable) and attr not in ["__new__", "__init__", "__int__", "__getattribute__", "__setattribute__",
                                               "__eq__", "__ne__", "__bool__", "__str__", "__repr__", "__getnewargs__"]:
                setattr(IntParameter, attr, none_decorator(func))
        return val

    def __init__(self, name, help, default=None, type=int, choices=None, required=False,
                 flag=None, sub_parameters=None, group="default", display_name=None, cmd_format="", argpos=-1):
        AbstractParameter.__init__( self, name, help, flag=flag, default=default, type=type, choices=choices, required=required,
                                    action="store", sub_parameters=sub_parameters, group=group, display_name=display_name,  cmd_format=cmd_format, argpos=argpos)

    def __getnewargs__(self):
        return (self.name, self.help, self.default, self.type, self.choices, self.required, self.flag,
                self.sub_parameters, self.group, self.display_name, self.cmd_format, self.argpos)

    def __str__(self):
        if self.is_None:
            return str(None)
        return str(int(self))

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if other.__class__.__name__ == "NoneType":
            return self.is_None
        elif self.is_None:
            return False
        else:
            return int(self) == int(other)

    def __ne__(self, other):
        return not (self == other)

    def __bool__(self):
        if self.is_None:
            return False
        else:
            return self != 0


class FloatParameter(float, AbstractParameter):

    def __new__(self, name, help, default=None, type=float, choices=None, required=False,
                flag=None, sub_parameters=None, group="default", display_name=None, cmd_format="", argpos=-1):
        float_default = 0.0 if default == None else float(default)
        val = float.__new__(self, float_default)
        val.is_None = False if default != None else True
        for attr in float.__dict__:
            func = getattr(float, attr)
            if isinstance(func, collections.Callable) and attr not in ["__new__", "__init__", "__float__", "__getattribute__", "__setattribute__", 
                                               "__eq__", "__ne__", "__bool__", "__str__", "__repr__", "__getnewargs__"]:
                setattr(FloatParameter, attr, none_decorator(func))
        return val

    def __init__(self, name, help, default=None, type=float, choices=None, required=False,
                 flag=None, sub_parameters=None, group="default", display_name=None, cmd_format="", argpos=-1):
        AbstractParameter.__init__(self, name, help, flag=flag, default=default, type=type, choices=choices, required=required, 
                                   action="store", sub_parameters=sub_parameters, group=group, display_name=display_name,cmd_format=cmd_format, argpos=argpos )

    def __getnewargs__(self):
        return (self.name, self.help, self.default, self.type, self.choices, self.required, self.flag,
                self.sub_parameters, self.group, self.display_name, self.cmd_format, self.argpos)

    def __str__(self):
        if self.is_None:
            return str(None)
        return str(float(self))

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if other.__class__.__name__ == "NoneType":
            return self.is_None
        elif self.is_None:
            return False
        else:
            return float(self) == float(other)

    def __ne__(self, other):
        return not (self == other)

    def __bool__(self):
        if self.is_None:
            return False
        else:
            return self != 0.0


class StrParameter(str, AbstractParameter):

    def __new__(self, name, help, default=None, type=str, choices=None, required=False,
                flag=None, sub_parameters=None, group="default", display_name=None, cmd_format="", argpos=-1):
        str_default = "" if default == None else str(default)
        val = str.__new__(self, str_default)
        val.is_None = False if default != None else True
        for attr in str.__dict__:
            func = getattr(str, attr)
            if isinstance(func, collections.Callable) and attr not in ["__new__", "__init__", "__str__", "__getattribute__", "__setattribute__",
                                               "__eq__", "__ne__", "__bool__", "__repr__", "__getnewargs__"]:                
                setattr(StrParameter, attr, none_decorator(func))
        return val

    def __init__(self, name, help, default=None, type=str, choices=None, required=False,
                 flag=None, sub_parameters=None, group="default", display_name=None, cmd_format="", argpos=-1):
        AbstractParameter.__init__(self, name, help, flag=flag, default=default, type=type, choices=choices, required=required, 
                                   action="store", sub_parameters=sub_parameters, group=group, display_name=display_name, cmd_format=cmd_format, argpos=argpos)        
        
    def __getnewargs__(self):
        return (self.name, self.help, self.default, self.type, self.choices, self.required, self.flag,
                self.sub_parameters, self.group, self.display_name, self.cmd_format, self.argpos)

    def __str__(self):
        if self.is_None:
            return str(None)
        return str.__str__(self)

    def __repr__(self):
        if self.is_None:
            return str(None)
        return "'" + str(self) + "'"

    def __eq__(self, other):
        if other.__class__.__name__ == "NoneType":
            return self.is_None
        elif self.is_None:
            return False
        else:
            return str(self) == str(other)

    def __ne__(self, other):
        return not(self == other)

    def __bool__(self):
        if self.is_None:
            return False
        else:
            return (True if str(self) else False)

class PasswordParameter(StrParameter):
    def __new__(self, name, help, default=None, type="password", choices=None, required=False,
                flag=None, sub_parameters=None, group="default", display_name=None, cmd_format="", argpos=-1):
        return StrParameter.__new__(self, name, help, flag=flag, default=default, type=type, choices=choices,
                           required=required, group=group, display_name=display_name, cmd_format=cmd_format, argpos=argpos)

    def __init__(self, name, help, default=None, type="password", choices=None, required=False,
                 flag=None, sub_parameters=None, group="default", display_name=None, cmd_format="", argpos=-1):
        StrParameter.__init__(self, name, help, flag=flag, default=default, type=type, choices=choices, required=required, 
                                   sub_parameters=sub_parameters, group=group, display_name=display_name, cmd_format=cmd_format, argpos=argpos) 

    @staticmethod
    def __rc4(data, key):
        S = list(range(256))
        j = 0
        out = []
        
        #KSA Phase
        for i in range(256):
            j = (j + S[i] + ord( key[i % len(key)] )) % 256
            S[i] , S[j] = S[j] , S[i]
        
        #PRGA Phase
        i = j = 0
        for char in data:
            i = ( i + 1 ) % 256
            j = ( j + S[i] ) % 256
            S[i] , S[j] = S[j] , S[i]
            out.append(chr(ord(char) ^ S[(S[i] + S[j]) % 256]))
            
        return ''.join(out)

    @staticmethod
    def encrypt(data, key="anything", salt_length=16):
        salt = ''
        for n in range(salt_length):
            salt += chr(random.randrange(256))
        data = salt + PasswordParameter.__rc4(data, key + salt)
        return urllib.parse.quote(data)

    @staticmethod
    def decrypt(data, key="anything", salt_length=16):
        #data = base64.b64decode(data.encode()).decode()
        data = urllib.parse.unquote(data)
        salt = data[:salt_length]
        return PasswordParameter.__rc4(data[salt_length:], key + salt)


class DateParameter(datetime.datetime, AbstractParameter):

    def __new__(self, name, help, default=None, type=date, choices=None, required=False,
                flag=None, sub_parameters=None, group="default", display_name=None, cmd_format="", argpos=-1):
        date_default = datetime.datetime.today()
        if default != None and issubclass(default.__class__, datetime.datetime):
            date_default = default
        elif default != None:
            date_default = date(default)
        val = datetime.datetime.__new__(self, date_default.year, date_default.month, date_default.day)
        val.is_None = False if default != None else True
        for attr in datetime.datetime.__dict__:
            func = getattr(datetime.datetime, attr)
            if isinstance(func, collections.Callable) and attr not in ["__new__", "__init__", "__getattribute__", "__setattribute__",
                                               "__eq__", "__ne__", "__bool__", "__str__", "__repr__", "__getnewargs__"]:
                setattr(DateParameter, attr, none_decorator(func))
        return val

    def __init__(self, name, help, default=None, type=date, choices=None, required=False,
                 flag=None, sub_parameters=None, group="default", display_name=None, cmd_format="", argpos=-1):
        if default != None and not issubclass(default.__class__, datetime.datetime):
            date_default = date(default)
            default = datetime.datetime(date_default.year, date_default.month, date_default.day)
        AbstractParameter.__init__(self, name, help, flag=flag, default=default, type=type, choices=choices, required=required, 
                                   action="store", sub_parameters=sub_parameters, group=group, display_name=display_name, cmd_format=cmd_format, argpos=argpos)

    def __getnewargs__(self):
        return (self.name, self.help, self.default, self.type, self.choices, self.required, self.flag,
                self.sub_parameters, self.group, self.display_name, self.cmd_format, self.argpos)

    def __str__(self):
        if self.is_None:
            return str(None)
        return datetime.datetime.__str__(self)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if other.__class__.__name__ == "NoneType":
            return self.is_None
        elif self.is_None:
            return False
        else:
            return datetime.date(self.year, self.month, self.day) == other

    def __ne__(self, other):
        return not( self == other )

    def __bool__(self):
        if self.is_None:
            return False
        else:
            return (True if datetime.date(self.year, self.month, self.day) else False)

    def __reduce__(self):
        return (DateParameter, (self.name, self.help, self.default, date, self.choices, self.required,
                 self.flag, self.sub_parameters, self.group, self.display_name), None, None, None)

    def __reduce_ex__(self, protocol):
        return (DateParameter, (self.name, self.help, self.default, date, self.choices, self.required,
                 self.flag, self.sub_parameters, self.group, self.display_name), None, None, None)

def input_directory_get_files_fn(input):
    return os.listdir(input)

class InputDirectory(StrParameter, LinkTraceback):

    def __new__(self, name, help, default="", choices=None, required=False, flag=None, 
                group="default", display_name=None, get_files_fn=None, cmd_format="", argpos=-1):
        return StrParameter.__new__(self, name, help, flag=flag, default=default, type="inputdirectory", choices=choices, 
                           required=required, group=group, display_name=display_name, cmd_format=cmd_format, argpos=argpos)

    def __init__(self, name, help, default="", choices=None, required=False, flag=None, 
                group="default", display_name=None, get_files_fn=None, cmd_format="", argpos=-1):
        LinkTraceback.__init__(self)
        StrParameter.__init__(self, name, help, flag=flag, default=default, type="inputdirectory", choices=choices, 
                           required=required, group=group, display_name=display_name, cmd_format=cmd_format, argpos=argpos)
        if hasattr(get_files_fn, "__call__"):
            self.get_files_fn = get_files_fn
        else:
            self.get_files_fn = input_directory_get_files_fn

    def __getnewargs__(self):
        return (self.name, self.help, self.default, self.choices, self.required, self.flag,
                self.group, self.display_name, self.get_files_fn, self.cmd_format, self.argpos)

    def prepare(self, input):
        if input == None:
            return None
        return os.path.abspath(input)
    
    def get_files(self, *args):
        files = []
        for file in self.get_files_fn(self, *args):
            files.append( IOFile(os.path.join(self, file), "any", self.linkTrace_nameid, None) )
        return files
    
class AbstractInputFile(AbstractIOFile):
    """
     @summary : Parent of all InputFile(s) parameters.
    """
    
    SIZE_LIMIT_SPLITER = "__sl"
    
    def __init__(self, file_format="any", size_limit="0"):
        AbstractIOFile.__init__(self, file_format)
        self.size_limit = size_limit
    
    def _download_urlfile(self, input):
        try:
            uri_object = urlparse(input)
            opener = urlopen(input)
            block_size = 8000
            jflowconf = JFlowConfigReader()
            tmp_directory = os.path.join(jflowconf.get_tmp_directory(), os.path.basename(tempfile.NamedTemporaryFile().name))
            os.mkdir(tmp_directory) 
            file_path = os.path.join(tmp_directory, os.path.basename(uri_object.path))
            if os.path.basename(uri_object.path) is not None and os.path.basename(uri_object.path) != "":
                local_file = open(file_path, 'wb')
                metadata = opener.info()
                file_size = int(metadata.getheaders("Content-Length")[0])
                while True:
                    buffer = opener.read(block_size)
                    # End of download
                    if not buffer: break
                    # Parts of download
                    local_file.write(buffer)
                local_file.close()
                logging.getLogger("jflow").debug("URL file '{0}' successfully downloaded as: {1}".format(input, file_path))
            return [file_path, True]
        except:
            return [input, False]

    def check(self, ifile):
        try:
            eval(self.file_format)
            function_exists = True
        except: function_exists = False
        if function_exists:
            try: 
                eval(self.file_format)(ifile)
            except jflow.InvalidFormatError as e:
                raise Exception (str(e))
        else:
            raise Exception("Invalid file format '" + self.file_format + "'!")

class AbstractOutputFile(AbstractIOFile):
    """
     @summary : Parent of all OutputFile(s) parameters.
    """
    pass


class InputFile(StrParameter, AbstractInputFile):

    def __new__(self, name, help, file_format="any", default="", type="localfile", choices=None, 
                required=False, flag=None, group="default", display_name=None, size_limit="0",  cmd_format="", argpos=-1):
        if hasattr(type, '__call__'):
            type2test = type.__name__
        else: type2test = type

        if type2test not in INPUTFILE_TYPES:
            raise ValueError("InputFile.__new__: wrong type provided: '"+type2test+"', this should be choosen between '" 
                             + "', '".join(INPUTFILE_TYPES)+"'")

        return StrParameter.__new__(self, name, help, flag=flag, default=default, type=type, choices=choices, 
                           required=required, group=group, display_name=display_name, cmd_format=cmd_format, argpos=argpos)

    def __init__(self, name, help, file_format="any", default="", type="localfile", choices=None, 
                required=False, flag=None, group="default", display_name=None, size_limit="0",  cmd_format="", argpos=-1):
        AbstractInputFile.__init__(self, file_format, size_limit)
        if issubclass(default.__class__, list):
            raise Exception( "The parameter '" + name + "' cannot be set with a list." )
        StrParameter.__init__(self, name, help, flag=flag, default=default, type=type, choices=choices, 
                           required=required, group=group, display_name=display_name, cmd_format=cmd_format, argpos=argpos)

    def __getnewargs__(self):
        return (self.name, self.help, self.file_format, self.default, self.type, self.choices, self.required, 
                self.flag, self.group, self.display_name, self.size_limit, self.cmd_format, self.argpos)

    def get_type(self):
        return self.type.__name__+AbstractInputFile.SIZE_LIMIT_SPLITER+self.size_limit

    def get_test_function(self):
        if (self.size_limit == "0"): ctype = self.type
        else: ctype = self.get_type()
        return create_test_function(ctype)

    def prepare(self, input):
        if input == None:
            return None
        # handle url inputs
        new_path, is_uri = self._download_urlfile(input)
        # handle upload inputs
        try: is_local = os.path.isfile(input)
        except: is_local = False
        if not is_uri and not is_local and self.type.__name__ == "inputfile" or self.type.__name__ == "browsefile":
            jflow_config_reader = JFlowConfigReader()
            new_path = os.path.join(jflow_config_reader.get_tmp_directory(), input)
        if is_local: new_path = os.path.abspath(input)
        self.check(new_path)
        return new_path


class OutputFile(StrParameter, AbstractOutputFile):

    def __new__(self, name, help, file_format="any", default="", choices=None,
                required=False, flag=None, group="default", display_name=None, 
                cmd_format="", argpos=-1):
        return StrParameter.__new__(self, name, help, flag=flag, default=default, type="localfile", choices=choices,
                           required=required, group=group, display_name=display_name, cmd_format=cmd_format, argpos=argpos)

    def __init__(self, name, help, file_format="any", default="", choices=None,
                required=False, flag=None, group="default", display_name=None,
                cmd_format="", argpos=-1):
        AbstractIOFile.__init__(self, file_format)
        if issubclass(default.__class__, list):
            raise Exception( "The parameter '" + name + "' cannot be set with a list." )
        StrParameter.__init__(self, name, help, flag=flag, default=default, type="localfile", choices=choices, 
                           required=required, group=group, display_name=display_name, cmd_format=cmd_format, argpos=argpos)
    
    def __getnewargs__(self):
        return (self.name, self.help, self.file_format, self.default, self.choices, self.required, 
                self.flag, self.group, self.display_name, self.cmd_format, self.argpos)
        

class ParameterList(list, AbstractParameter):

    def __init__(self, name, help, default=None, type=str, choices=None, required=False,
                 flag=None, sub_parameters=None, group="default", display_name=None,
                  cmd_format="", argpos=-1):
        if default == None: default = []
        AbstractParameter.__init__(self, name, help, flag=flag, default=default, type=type, choices=choices, required=required,
                                   action="append", sub_parameters=sub_parameters, group=group, display_name=display_name,
                                   cmd_format=cmd_format, argpos=argpos)
        liste = []
        if isinstance( default, list ):
            for val in default :
                liste.append(ParameterFactory.factory( name, help, default=val, type=type, choices=choices, 
                      required=required, flag=flag, group=group, display_name=display_name ))
        else :
            liste.append(ParameterFactory.factory( name, help, default=default, type=type, choices=choices, 
                      required=required, flag=flag, group=group, display_name=display_name ))
        return list.__init__(self, liste)
        
    def append(self, item):
        raise TypeError('A parameter is immutable.')

    def extend(self, items):
        raise TypeError('A parameter is immutable.')


class InputFileList(ParameterList, AbstractInputFile):

    def __init__(self, name, help, file_format="any", default=None, type="localfile", choices=None, 
                 required=False, flag=None, group="default", display_name=None, size_limit="0",
                 cmd_format="", argpos=-1):

        if default == None: default = []
        if hasattr(type, '__call__'):
            if type.__name__ == "inputfile":
                type = inputfiles
            type2test = type.__name__
        else:
            if type == "inputfile":
                type = "inputfiles"
            type2test = type
        if type2test not in INPUTFILES_TYPES:
            raise ValueError("InputFile.__new__: wrong type provided: '"+type2test+"', this should be choosen between '" 
                             + "', '".join(INPUTFILE_TYPES)+"'")

        AbstractInputFile.__init__(self, file_format, size_limit)
        ParameterList.__init__(self, name, help, flag=flag, default=default, type=type, choices=choices, 
                               required=required, group=group, display_name=display_name,
                               cmd_format=cmd_format, argpos=argpos)

        if default.__class__.__name__ == "str":
            return list.__init__(self, [default])
        elif default.__class__.__name__ == "list":
            return list.__init__(self, default)
        elif issubclass( default.__class__, InputFile ):
            return list.__init__(self, [default])
        elif issubclass( default.__class__, AbstractInputFile ):
            return list.__init__(self, default)
        elif issubclass( default.__class__, OutputFile ):
            return list.__init__(self, [default])
        elif issubclass( default.__class__, AbstractOutputFile ):
            return list.__init__(self, default)
    
    def get_type(self):
        return self.type.__name__+AbstractInputFile.SIZE_LIMIT_SPLITER+self.size_limit
    
    def get_test_function(self):
        if (self.size_limit == "0"): ctype = self.type
        else: ctype = self.get_type()
        return create_test_function(ctype)

    def prepare(self, inputs):
        path2test = _copy.deepcopy(inputs)
        new_vals = list()
        if not path2test.__class__.__name__ == "list":
            path2test = [path2test]
        for path in path2test:
            new_url, is_uri = self._download_urlfile(path)
            if is_uri: # handle url inputs
                new_vals.append(new_url)
            elif os.path.isfile(path): # handle localfile
                new_vals.append(os.path.abspath(path))
            else:
                try: # handle regexp files
                    regexpfiles(path)
                    if ':' in path:
                        folder, pattern = path.rsplit(':')
                    else:
                        folder, pattern = os.path.split(path)
                    for item in sorted(os.listdir(folder)):
                        if os.path.isfile(os.path.join(folder, item)) and fnmatch.fnmatch(item, pattern):
                            new_vals.append( os.path.abspath(os.path.join(folder, item)) )
                except: # handle upload inputs
                    jflow_config_reader = JFlowConfigReader()
                    new_vals.append(os.path.join(jflow_config_reader.get_tmp_directory(), path))
        # now that all files are downloaded and ok, check the format
        for cfile in new_vals:
            self.check(cfile)
        return new_vals

class OutputFileList(ParameterList, AbstractOutputFile):

    def __init__(self, name, help, file_format="any", default=None, choices=None, 
                 required=False, flag=None, group="default", display_name=None,
                 cmd_format="", argpos=-1):
        if default == None: default = []
        AbstractIOFile.__init__(self, file_format)
        ParameterList.__init__(self, name, help, flag=flag, default=default, type="localfile", choices=choices, 
                               required=required, group=group, display_name=display_name,
                               cmd_format=cmd_format, argpos=argpos)
        if default.__class__.__name__ == "str":
            return list.__init__(self, [default])
        elif default.__class__.__name__ == "list":
            return list.__init__(self, default)


class DynamicOutput(ParameterList, AbstractOutputFile):
    """
     @warning : with this class of output, the component become dynamic.
    """
    def update(self):
        """
         This method is used at the end of component execution to update output list.
        """
        raise NotImplementedError


class OutputFilesEndsWith(DynamicOutput):

    def __init__(self, name, help, output_directory, end_str, include=True, file_format="any", choices=None, 
                 required=False, flag=None, group="default", display_name=None, cmd_format="", argpos=-1):
        """
         @warning : with this class of output, the component become dynamic.
         @param output_directory : path to the directory where outputs will be created.
         @param end_str : the end of the files names.
         @param include : if true, the files with name terminated by end_str are added into output files.
                          If false, the files with name not terminated by end_str are added into output files.
        """
        AbstractIOFile.__init__(self, file_format)
        default = []
        ParameterList.__init__(self, name, help, flag=flag, default=default, type="localfile", choices=choices, 
                               required=required, group=group, display_name=display_name, cmd_format=cmd_format, 
                               argpos=argpos)
        self.output_directory = output_directory
        self.end_str = end_str
        self.include = include
        return list.__init__(self, default)

    def update(self):
        output_files = list()
        for file in os.listdir( self.output_directory ):
            if file.endswith( self.end_str ) and self.include :
                output_files.append( IOFile(os.path.join(self.output_directory, file), self.file_format, self.linkTrace_nameid, None) )
            elif not file.endswith( self.end_str ) and not self.include:
                output_files.append( IOFile(os.path.join(self.output_directory, file), self.file_format, self.linkTrace_nameid, None) )
        list.__init__(self, output_files)


class OutputFilesPattern(DynamicOutput):

    def __init__(self, name, help, output_directory, pattern, include=True, file_format="any", choices=None, 
                  required=False, flag=None, group="default", display_name=None, cmd_format="", argpos=-1):
        """
         @warning : with this class of output, the component become dynamic.
         @param output_directory : path to the directory where outputs will be created.
         @param pattern : the pattern of (a part) the file names.
         @param include : if true, the files with the pattern in file name are added into output files.
                          If false, the files with the pattern in file name are added into output files.
        """
        AbstractIOFile.__init__(self, file_format)
        default = []
        ParameterList.__init__(self, name, help, flag=flag, default=default, type="localfile", choices=choices, 
                               required=required, group=group, display_name=display_name, cmd_format=cmd_format, 
                               argpos=argpos)
        self.output_directory = output_directory
        self.pattern = pattern
        self.include = include
        return list.__init__(self, default)

    def update(self):
        output_files = list()
        for file in os.listdir( self.output_directory ):
            if self.include and re.search( self.pattern, file ) is not None:
                output_files.append( IOFile(os.path.join(self.output_directory, file), self.file_format, self.linkTrace_nameid, None) )
            elif not self.include and re.search( self.pattern, file ) is None:
                output_files.append( IOFile(os.path.join(self.output_directory, file), self.file_format, self.linkTrace_nameid, None) )
        return list.__init__(self, output_files)
    
    
    
class IOObject(object):
    
    IOOBJECT_EXT = ".ioobj"
    
    @staticmethod
    def add_required_attributs(obj):
        jflowconf = JFlowConfigReader()

        obj.is_ioobject = True
        obj.dump_path = os.path.join(jflowconf.get_tmp_directory(), os.path.basename(tempfile.NamedTemporaryFile(suffix=IOObject.IOOBJECT_EXT).name))
        obj.includes = []
        obj.linkTrace_nameid = None
        obj.parent_linkTrace_nameid = []
    
    def __init__(self):
        IOObject.add_required_attributs(self)
    
    
class IObjectList(list, IOObject):
    
    def __new__(self, value):
        val = list.__new__(self)
        val.extend(value)
        return val
    
    def __init__(self, value):
        IOObject.__init__(self)
        
        for cobj in value:
            if isinstance(cobj, OObject):
                self.includes.append(cobj.dump_path)
            if isinstance(cobj, InputFile) or isinstance(cobj, OutputFile) :
                self.includes.append(cobj)
            if isinstance(cobj, list): # list of list
                for elt in cobj:
                    if issubclass(elt.__class__, AbstractIOFile) and issubclass(elt.__class__, ParameterList) :
                        self.includes.extend(elt)
                    elif issubclass(elt.__class__, AbstractIOFile) :
                        self.includes.append(elt)
            if isinstance(cobj, dict): # list of dict
                for ckey,cval in list(cobj.items()):
                    if issubclass(cval.__class__, AbstractIOFile) and issubclass(cval.__class__, ParameterList) :
                        self.includes.extend(cval)
                    elif issubclass(cval.__class__, AbstractIOFile) :
                        self.includes.append(cval)
            
    def __getnewargs__(self):
        return (self)
    
        
class IObjectDict(dict, IOObject):
    
    def __new__(self, value):
        val = dict.__new__(self, value)
        for ckey in list(value.keys()): val[ckey] = value[ckey]
        return val
    
    def __init__(self, value):
        IOObject.__init__(self)
        for ckey,value in list(value.items()):
            if isinstance(value, OObject):
                self.includes.append(value.dump_path)
            if isinstance(value, InputFile) or isinstance(value, OutputFile) :
                self.includes.append(value)
            if isinstance(value, list): # list of list
                if issubclass(value.__class__, AbstractIOFile) and issubclass(value.__class__, ParameterList) :
                    self.includes.extend(value)
                elif issubclass(value.__class__, AbstractIOFile) :
                    self.includes.append(value)
            if isinstance(value, dict): # list of dict
                for k,cval in list(cobj.items()):
                    if issubclass(cval.__class__, AbstractIOFile) and issubclass(cval.__class__, ParameterList) :
                        self.includes.extend(cval)
                    elif issubclass(cval.__class__, AbstractIOFile) :
                        self.includes.append(cval)

    def __getnewargs__(self):
        return (self)


class IObjectFactory(object):
    
    @staticmethod
    def factory(obj):
        new_obj = None
        to_pickle = True
        if isinstance(obj, OObject):
            to_pickle = False
            new_obj = obj
        elif isinstance(obj, list):
            new_obj = IObjectList(obj)
        elif isinstance(obj, dict):
            new_obj = IObjectDict(obj)
        else:
            new_obj = obj
            IOObject.add_required_attributs(new_obj)
            
        if to_pickle:
            ioobjh = open(new_obj.dump_path, "wb")
            pickle.dump(new_obj, ioobjh)
            ioobjh.close()
            
        return new_obj

class OObject(IOObject): 
    def load(self):
        if os.path.exists(self.dump_path):
            fh = open(self.dump_path, 'rb')
            o=pickle.load(fh)
            fh.close()
            return o

class InputObject(AbstractParameter, LinkTraceback):
    
    def __init__( self, name, help, default=None, required=False):
        new_object = IObjectFactory.factory(default)
        AbstractParameter.__init__(self, name, help, default=new_object, type="object", required=required, action="store")
        LinkTraceback.__init__(self)

class InputObjectList(ParameterList, LinkTraceback) :
    
    def __init__ (self, name, help, default=None, required=False) :
        
        new_default = []
        if isinstance(default, list):
            if len(default)>0 :
                objects_class = default[0].__class__.__name__
                for cobj in default:
                    if objects_class != cobj.__class__.__name__:
                        raise Exception('All object in an InputObjectList should have the same type!')
                        
            for obj in default:
                new_obj = IObjectFactory.factory(obj)
                new_default.append(new_obj)
        else :
            new_obj = IObjectFactory.factory(default)
            new_default = [new_obj]
        ParameterList.__init__(self, name, help, default=new_default, type="object", required=required)
        LinkTraceback.__init__(self)

class OutputObject(AbstractParameter, LinkTraceback):
    
    def __init__( self, name, help, required=False):
        AbstractParameter.__init__(self, name, help, default=OObject(), type="object", required=required, action="store")
        LinkTraceback.__init__(self)

class OutputObjectList(ParameterList, LinkTraceback) :
    
    def __init__ (self, name, help, nb_items=0, required=False) :
        new_default = [ OObject() for i in range(nb_items) ]
        ParameterList.__init__(self, name, help, default=new_default, type="object", required=required)
        LinkTraceback.__init__(self)
