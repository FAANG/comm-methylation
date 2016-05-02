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

import inspect
import os
import re
import sys
import uuid
import pkgutil
import tempfile
import pickle
import time
import threading
import types
import datetime
import logging
import traceback

from configparser import ConfigParser, NoOptionError
from inspect import getcallargs
from datetime import date as ddate

import jflow
import jflow.utils as utils
from jflow.utils import validate_email
from pygraph.classes.digraph import digraph
from jflow.workflows_manager import WorkflowsManager 
from jflow.config_reader import JFlowConfigReader
from jflow.utils import get_octet_string_representation, get_nb_octet
from jflow.parameter import *
from cctools.util import time_format

from weaver.script import ABSTRACTIONS
from weaver.script import DATASETS
from weaver.script import FUNCTIONS
from weaver.script import NESTS
from weaver.script import OPTIONS
from weaver.script import STACKS
from weaver.nest import Nest
from weaver.options import Options
from cctools.makeflow import MakeflowLog
from cctools.makeflow.log import Node


class MINIWorkflow(object):
    
    def __init__(self, id, name, description, status, start_time, end_time, metadata, 
                 component_nameids, compts_status, errors):
        self.id = id
        self.name = name
        self.description = description
        self._status = status
        self.start_time = start_time
        self.end_time = end_time
        self.metadata = metadata
        self.component_nameids = component_nameids
        self.compts_status = compts_status
        self.errors = errors
        
    def get_components_nameid(self):
        return self.component_nameids

    def get_components_status(self):
        return self.compts_status
    
    def get_component_status(self, component_nameid):
        return self.compts_status[component_nameid]
    
    def get_errors(self):
        return self.errors
    
    def get_status(self):
        return self._status

class Workflow(threading.Thread):
    
    MAKEFLOW_LOG_FILE_NAME = "Makeflow.makeflowlog"
    DUMP_FILE_NAME = ".workflow.dump"
    STDERR_FILE_NAME = "wf_stderr.txt"
    WORKING = ".working"
    OLD_EXTENSION = ".old"
    DEFAULT_GROUP = "default"
    
    STATUS_PENDING = "pending"
    STATUS_STARTED = "started"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_ABORTED = "aborted"
    STATUS_RESETED = "reseted"
    
    INPUTFILE_GRAPH_LABEL = "inputfile"
    INPUTFILES_GRAPH_LABEL = "inputfiles"
    INPUTDIRECTORY_GRAPH_LABEL = "inputdirectory"
    COMPONENT_GRAPH_LABEL = "component"
    
    
    def __init__(self, args={}, id=None, function= "process"):
        # define as a thread
        threading.Thread.__init__(self)
        self.jflow_config_reader = JFlowConfigReader()
        self.manager = WorkflowsManager()
        self.components_to_exec = []
        self.components = []
        self.makes = {}
        self.globals = {}
        self.options = Options()
        self._status = self.STATUS_STARTED
        self._postprocess_status = self.STATUS_PENDING
        self.start_time = None
        self.end_time = None
        self.__step = None
        self.stderr = None
        self.args = args
        self.dynamic_component_present = False
        self.__to_address = None
        self.__subject = None
        self.__message = None
        self.function = function
        # intruduce --log-verbose to be able to monitor the new version of makeflow >=4.2.2
        self.engine_arguments = ' --log-verbose '
        self.component_nameids_is_init = False
        self.component_nameids = {}
        self.reseted_components = []
        # try to parse engine arguments
        try:
            type, options, limit_submission = self.jflow_config_reader.get_batch()
            if limit_submission : self.engine_arguments += ' -J ' + str(limit_submission)
            if type: self.engine_arguments += ' -T ' + type
            if options : self.engine_arguments += ' -B "' + options + '"'
        except: self.engine_arguments = None

        self.id = id
        self.name = self.get_name()
        self.description = self.get_description()
        self.__group = self.jflow_config_reader.get_workflow_group(self.__class__.__name__) or Workflow.DEFAULT_GROUP
        
        # define the parameters 
        self.params_order = []
        if self.function != None:
            self.define_parameters(self.function)
        # add the metadata parameter
        self.metadata = []
        
        if self.id is not None:
            self.directory = self.manager.get_workflow_directory(self.name, self.id)
            if not os.path.isdir(self.directory):
                os.makedirs(self.directory, 0o751)
            if self.stderr is None:
                self.stderr = self._set_stderr()
            self._serialize()
            
        self.internal_components = self._import_internal_components()
        self.external_components = self._import_external_components()

    def get_workflow_group(self):
        return self.__group
            
    def add_input_directory(self, name, help, default=None, required=False, flag=None, 
                            group="default", display_name=None, get_files_fn=None, add_to=None):
        new_param = InputDirectory(name, help, flag=flag, default=default, required=required, 
                                   group=group, display_name=display_name, get_files_fn=get_files_fn)
        new_param.linkTrace_nameid = name
        # if this input should be added to a particular parameter
        if add_to:
            try:
                self.__getattribute__(add_to).add_sub_parameter(new_param)
            except: pass
        # otherwise, add it to the class itself
        else:
            self.params_order.append(name)
            self.__setattr__(name, new_param)
    
    def add_input_file(self, name, help, file_format="any", default=None, type="inputfile", 
                       required=False, flag=None, group="default", display_name=None, size_limit="0", add_to=None):
        # check if the size provided is correct
        try: int(get_nb_octet(size_limit))
        except: size_limit="0"
        new_param = InputFile(name, help, flag=flag, file_format=file_format, default=default, 
                              type=type, required=required, group=group, display_name=display_name, size_limit=size_limit)
        new_param.linkTrace_nameid = name
        # if this input should be added to a particular parameter
        if add_to:
            try:
                self.__getattribute__(add_to).add_sub_parameter(new_param)
            except: pass
        # otherwise, add it to the class itself
        else:
            self.params_order.append(name)
            self.__setattr__(name, new_param)
            
    def add_input_file_list(self, name, help, file_format="any", default=None, type="inputfile", 
                            required=False, flag=None, group="default", display_name=None, size_limit="0", add_to=None):
        # check if the size provided is correct
        if default == None: default = []
        try: int(get_nb_octet(size_limit))
        except: size_limit="0"
        if default == None:
            inputs = []
        elif issubclass(default.__class__, list):
            inputs = [IOFile(file, file_format, name, None) for file in default]
        else:
            inputs = [IOFile(default, file_format, name, None)]
        new_param = InputFileList(name, help, flag=flag, file_format=file_format, default=inputs, 
                                  type=type, required=required, group=group, display_name=display_name, size_limit=size_limit)
        new_param.linkTrace_nameid = name
        # if this input should be added to a particular parameter
        if add_to:
            try:
                self.__getattribute__(add_to).add_sub_parameter(new_param)
            except: pass
        # otherwise, add it to the class itself
        else:
            self.params_order.append(name)
            self.__setattr__(name, new_param)
            
    def add_multiple_parameter(self, name, help, required=False, flag=None, group="default", display_name=None):
        self.params_order.append(name)
        new_param = MultiParameter(name, help, flag=flag, required=required, group=group, display_name=display_name)
        self.__setattr__(name, new_param)

    def add_multiple_parameter_list(self, name, help, required=False, flag=None, group="default", display_name=None):
        self.params_order.append(name)
        new_param = MultiParameterList(name, help, flag=flag, required=required, group=group, display_name=display_name)
        self.__setattr__(name, new_param)
    
    def add_parameter(self, name, help, default=None, type=str, choices=None, 
                      required=False, flag=None, group="default", display_name=None, add_to=None):
        new_param = ParameterFactory.factory(name, help, flag=flag, default=default, type=type, choices=choices, 
                              required=required, group=group, display_name=display_name)
        # if this input should be added to a particular parameter
        if add_to:
            try:
                self.__getattribute__(add_to).add_sub_parameter(new_param)
            except: pass
        # otherwise, add it to the class itself
        else:
            self.params_order.append(name)
            self.__setattr__(name, new_param)
    
    def add_parameter_list(self, name, help, default=None, type=str, choices=None, 
                           required=False, flag=None, group="default", display_name=None, add_to=None):
        if default == None: default = []
        new_param = ParameterList(name, help, flag=flag, default=default, type=type, choices=choices, 
                                  required=required, group=group, display_name=display_name)
        # if this input should be added to a particular parameter
        if add_to:
            try:
                self.__getattribute__(add_to).add_sub_parameter(new_param)
            except: pass
        # otherwise, add it to the class itself
        else:
            self.params_order.append(name)
            self.__setattr__(name, new_param)
    
    def add_exclusion_rule(self, *args2exclude):
        # first of all, does this parameter exist
        params2exclude = []
        for arg2exclude in args2exclude:
            try:
                params2exclude.append(self.__getattribute__(arg2exclude))
            except: pass
        # everything is ok, let's go
        if len(params2exclude) == len(args2exclude):
            new_group = "exclude-"+uuid.uuid4().hex[:5]
            for paramsexclude in params2exclude:
                paramsexclude.group = new_group
        # it might be a mutliple param rule
        else:
            self._log("Exclusion rule cannot be applied within a MultiParameter or a MultiParameterList", raisee=True)
        # save this for MultiParameter internal exclusion rules, works on command line, not supported on gui
#             for attribute_value in self.__dict__.values():
#                 if issubclass(attribute_value.__class__, MultiParameter) or issubclass(attribute_value.__class__, MultiParameterList):
#                     params2exclude = []
#                     for sub_param in attribute_value.sub_parameters:
#                         if sub_param.name in args2exclude:
#                             params2exclude.append(sub_param)
#                     if len(params2exclude) == len(args2exclude):
#                         new_group = "exclude-"+uuid.uuid4().hex[:5]
#                         flags2exclude = []
#                         for paramsexclude in params2exclude:
#                             paramsexclude.group = new_group
#                             flags2exclude.append(paramsexclude.flag)
#                         attribute_value.type.excludes[new_group] = flags2exclude
#                         break

    def _prepare_parameter(self, args, parameter, key="name"):
        new_param = None
        # Retrieve value
        if parameter.__getattribute__(key) in args:
            value = args[parameter.__getattribute__(key)]
        elif parameter.default != None:
            value = parameter.default
        else:
            value = None
        # Set new parameter
        if parameter.__class__ in [StrParameter, IntParameter, FloatParameter, BoolParameter, DateParameter, PasswordParameter]:
            if value == "" and parameter.__class__ in [IntParameter, FloatParameter, BoolParameter, DateParameter] : value = None # from GUI
            new_param = ParameterFactory.factory( parameter.name, parameter.help, default=value, type=parameter.type, choices=parameter.choices, 
                                                  required=parameter.required, flag=parameter.flag, group=parameter.group, 
                                                  display_name=parameter.display_name )
        elif parameter.__class__ ==  ParameterList:
            if value == "" : value = [] # from GUI
            new_param = ParameterList( parameter.name, parameter.help, default=value, type=parameter.type, choices=parameter.choices,
                                       required=parameter.required, flag=parameter.flag, sub_parameters=parameter.sub_parameters,
                                       group=parameter.group, display_name=parameter.display_name )
        elif parameter.__class__ == InputFileList:
            if value == "" : value = [] # from GUI
            iovalues = []
            prepared_files = parameter.prepare(value)
            for file in prepared_files:
                iovalues.append(IOFile(file, parameter.file_format, parameter.linkTrace_nameid, None))
            new_param = InputFileList( parameter.name, parameter.help, file_format=parameter.file_format, default=iovalues,
                                       type=parameter.type, choices=parameter.choices, required=parameter.required, flag=parameter.flag,
                                       group=parameter.group, display_name=parameter.display_name, size_limit=parameter.size_limit )
            new_param.linkTrace_nameid = parameter.linkTrace_nameid            
        elif parameter.__class__ == InputFile:
            if value == "" : value = None # from GUI
            prepared_file = parameter.prepare(value)
            new_param = InputFile( parameter.name, parameter.help, file_format=parameter.file_format, default=prepared_file,
                                   type=parameter.type, choices=parameter.choices, required=parameter.required, flag=parameter.flag, 
                                   group=parameter.group, display_name=parameter.display_name )
            new_param.linkTrace_nameid = parameter.linkTrace_nameid
        elif parameter.__class__ == InputDirectory:
            if value == "" : value = None # from GUI
            prepared_directory = parameter.prepare(value)
            new_param = InputDirectory( parameter.name, parameter.help, default=prepared_directory, choices=parameter.choices, 
                                        required=parameter.required, flag=parameter.flag, group=parameter.group, 
                                        display_name=parameter.display_name, get_files_fn=parameter.get_files_fn)
            new_param.linkTrace_nameid = parameter.linkTrace_nameid
        else:
            raise Exception( "Unknown class '" +  parameter.__class__.__name__ + "' for parameter.")
        return new_param

    def _set_parameters(self, args):
        parameters = self.get_parameters()
        for param in parameters:
            new_param = None
            if param.__class__ == MultiParameter:
                new_param = MultiParameter(param.name, param.help, required=param.required, flag=param.flag, group=param.group, display_name=param.display_name)
                new_param.sub_parameters = param.sub_parameters
                if param.name in args:
                    sub_args = {}
                    for sarg in args[param.name]:
                        sub_args[sarg[0]] = sarg[1]
                    for sub_param in param.sub_parameters:
                        new_sub_parameter = self._prepare_parameter(sub_args, sub_param, "flag")
                        new_param[new_sub_parameter.name] = new_sub_parameter
            elif param.__class__ == MultiParameterList:
                new_param = MultiParameterList(param.name, param.help, required=param.required, flag=param.flag, group=param.group, display_name=param.display_name)
                new_param.sub_parameters = param.sub_parameters
                if param.name in args:
                    for idx, sargs in enumerate(args[param.name]):
                        new_multi_param = MultiParameter(param.name + '_' + str(idx), '', required=False, flag=None, group="default", display_name=None)
                        sub_args = {}
                        for sarg in sargs:
                            sub_args[sarg[0]] = sarg[1]
                        for sub_param in param.sub_parameters:
                            new_sub_param = self._prepare_parameter(sub_args, sub_param, "flag")
                            new_multi_param[new_sub_param.name] = new_sub_param
                        new_param.append(new_multi_param)
            else:
                new_param = self._prepare_parameter(args, param)
            self.__setattr__(param.name, new_param)

    def get_execution_graph(self):
        gr = digraph()
        # build a all_nodes table to store all nodes
        all_nodes = {}
        for ioparameter in list(self.__dict__.values()):
            if issubclass(ioparameter.__class__, InputFile):
                gr.add_node(ioparameter.name)
                gr.add_node_attribute(ioparameter.name, self.INPUTFILE_GRAPH_LABEL)
                gr.add_node_attribute(ioparameter.name, ioparameter.display_name)
                all_nodes[ioparameter.name] = None
            elif issubclass(ioparameter.__class__, InputFileList):
                gr.add_node(ioparameter.name)
                gr.add_node_attribute(ioparameter.name, self.INPUTFILES_GRAPH_LABEL)
                gr.add_node_attribute(ioparameter.name, ioparameter.display_name)
                all_nodes[ioparameter.name] = None
            elif issubclass(ioparameter.__class__, InputDirectory):
                gr.add_node(ioparameter.name)
                gr.add_node_attribute(ioparameter.name, self.INPUTDIRECTORY_GRAPH_LABEL)
                gr.add_node_attribute(ioparameter.name, ioparameter.display_name)
                all_nodes[ioparameter.name] = None
            elif issubclass(ioparameter.__class__, MultiParameter):
                for subparam in ioparameter.sub_parameters:
                    gr.add_node(subparam.name)
                    all_nodes[subparam.name] = None
                    if issubclass(subparam.__class__, InputFile):
                        gr.add_node_attribute(subparam.name, self.INPUTFILE_GRAPH_LABEL)
                    elif issubclass(subparam.__class__, InputFileList):
                        gr.add_node_attribute(subparam.name, self.INPUTFILES_GRAPH_LABEL)
                    elif issubclass(subparam.__class__, InputDirectory):
                        gr.add_node_attribute(subparam.name, self.INPUTDIRECTORY_GRAPH_LABEL)
                    gr.add_node_attribute(subparam.name, subparam.display_name)
            elif issubclass(ioparameter.__class__, MultiParameterList):
                for subparam in ioparameter.sub_parameters:
                    gr.add_node(subparam.name)
                    all_nodes[subparam.name] = None                        
                    if issubclass(subparam.__class__, InputDirectory):
                        gr.add_node_attribute(subparam.name, self.INPUTDIRECTORY_GRAPH_LABEL)
                    else:
                        gr.add_node_attribute(subparam.name, self.INPUTFILES_GRAPH_LABEL)
                    gr.add_node_attribute(subparam.name, subparam.display_name)
        for cpt in self.components:
            gr.add_node(cpt.get_nameid())
            gr.add_node_attribute(cpt.get_nameid(), self.COMPONENT_GRAPH_LABEL)
            gr.add_node_attribute(cpt.get_nameid(), cpt.get_nameid())
            all_nodes[cpt.get_nameid()] = None
        for cpt in self.components:
            for ioparameter in list(cpt.__dict__.values()):
                if issubclass( ioparameter.__class__, InputFile ) or issubclass( ioparameter.__class__, InputFileList) or issubclass( ioparameter.__class__, InputDirectory):
                    for parent in ioparameter.parent_linkTrace_nameid:
                        try: gr.add_edge((parent, ioparameter.linkTrace_nameid))
                        except: pass
                elif issubclass( ioparameter.__class__, InputObject) or issubclass( ioparameter.__class__, InputObjectList):
                    for parent in ioparameter.parent_linkTrace_nameid:
                        try: gr.add_edge((parent, ioparameter.linkTrace_nameid))
                        except: pass
        # check if all nodes are connected
        for edge in gr.edges():
            if edge[0] in all_nodes:
                del all_nodes[edge[0]]
            if edge[1] in all_nodes:
                del all_nodes[edge[1]]
        # then remove all unconnected nodes: to delete inputs not defined by the user
        for orphan_node in list(all_nodes.keys()):
            gr.del_node(orphan_node)
        return gr

    def delete(self):
        if self.get_status() in [self.STATUS_COMPLETED, self.STATUS_FAILED, self.STATUS_ABORTED]:
            utils.robust_rmtree(self.directory)

    @staticmethod
    def config_parser(arg_lines):
        for arg in arg_lines:
            yield arg
            
    @staticmethod
    def get_status_under_text_format(workflow, detailed=False, display_errors=False, html=False):
        if workflow.start_time: start_time = time.asctime(time.localtime(workflow.start_time))
        else: start_time = "-"
        if workflow.start_time and workflow.end_time: elapsed_time = str(workflow.end_time-workflow.start_time)
        elif workflow.start_time: elapsed_time = str(time.time()-workflow.start_time)
        else: elapsed_time = "-"
        elapsed_time = "-" if elapsed_time == "-" else str(datetime.timedelta(seconds=int(str(elapsed_time).split(".")[0])))
        if workflow.end_time: end_time = time.asctime(time.localtime(workflow.end_time))
        else: end_time = "-"
        if detailed:
            # Global
            title = "Workflow #" + utils.get_nb_string(workflow.id) + " (" + workflow.name + ") is " + \
                    workflow.get_status() + ", time elapsed: " + str(elapsed_time) + " (from " + start_time + \
                    " to " + end_time + ")"
            worflow_errors = ""
            error = workflow.get_errors()
            if error is not None:
                if html: worflow_errors = "Workflow Error :\n  <span style='color:#ff0000'>" + error["location"] + "\n    " + "\n    ".join(error["msg"]) + "</span>"
                else: worflow_errors = "Workflow Error :\n  \033[91m" + error["location"] + "\n    " + "\n    ".join(error["msg"]) + "\033[0m"
            # By components
            components_errors = ""
            status = "Components Status :\n"
            components_status = workflow.get_components_status()
            for i, component in enumerate(workflow.get_components_nameid()):
                status_info = components_status[component]
                try: perc_waiting = (status_info["waiting"]*100.0)/status_info["tasks"]
                except: perc_waiting = 0
                try: perc_running = (status_info["running"]*100.0)/status_info["tasks"]
                except: perc_running = 0
                try: perc_failed = (status_info["failed"]*100.0)/status_info["tasks"]
                except: perc_failed = 0
                try: perc_aborted = (status_info["aborted"]*100.0)/status_info["tasks"]
                except: perc_aborted = 0
                try: perc_completed = (status_info["completed"]*100.0)/status_info["tasks"]
                except: perc_completed = 0
                
                if status_info["running"] > 0: 
                    if html: running = "<span style='color:#3b3bff'>running:" + str(status_info["running"]) + "</span>"
                    else: running = "\033[94mrunning:" + str(status_info["running"]) + "\033[0m"
                else: running = "running:" + str(status_info["running"])
                if status_info["waiting"] > 0: 
                    if html: waiting = "<span style='color:#ffea00'>waiting:" + str(status_info["waiting"]) + "</span>"
                    else: waiting = "\033[93mwaiting:" + str(status_info["waiting"]) + "\033[0m"
                else: waiting = "waiting:" + str(status_info["waiting"])            
                if status_info["failed"] > 0: 
                    if html: failed = "<span style='color:#ff0000'>failed:" + str(status_info["failed"]) + "</span>"
                    else: failed = "\033[91mfailed:" + str(status_info["failed"]) + "\033[0m"
                else: failed = "failed:" + str(status_info["failed"])
                if status_info["aborted"] > 0: 
                    if html: aborted = "<span style='color:#ff01ba'>aborted:" + str(status_info["aborted"]) + "</span>"
                    else: aborted = "\033[95maborted:" + str(status_info["aborted"]) + "\033[0m"
                else: aborted = "aborted:" + str(status_info["aborted"])
                if status_info["completed"] == status_info["tasks"] and status_info["completed"] > 0: 
                    if html: completed = "<span style='color:#14ac00'>completed:" + str(status_info["completed"]) + "</span>"
                    else: completed = "\033[92mcompleted:" + str(status_info["completed"]) + "\033[0m"
                else: completed = "completed:" + str(status_info["completed"])
                
                if display_errors and len(status_info["failed_commands"]) > 0:
                    if components_errors == "":
                        components_errors = "Failed Commands :\n"
                    components_errors += "  - " + component + " :\n    " + "\n    ".join(status_info["failed_commands"]) + "\n"
                status += "  - " + component + ", time elapsed " + time_format(status_info["time"]) + \
                    " (total:" + str(status_info["tasks"]) + ", " + waiting + ", " + running + ", " + failed + \
                    ", " + aborted + ", " + completed + ")"
                if i<len(workflow.get_components_nameid())-1: status += "\n"
            # Format str
            pretty_str = title
            pretty_str += ("\n" + worflow_errors) if worflow_errors != "" else ""
            if len(workflow.get_components_nameid()) > 0:
                pretty_str += ("\n" + status) if status != "" else ""
                pretty_str += ("\n" + components_errors[:-1]) if components_errors != "" else ""
            if html: return pretty_str.replace("\n", "<br />")
            else: return pretty_str
        else:
            pretty_str = utils.get_nb_string(workflow.id) + "\t" + workflow.name + "\t"
            if workflow.get_status() == Workflow.STATUS_STARTED:
                pretty_str += "\033[94m"
            elif workflow.get_status() == Workflow.STATUS_COMPLETED:
                pretty_str += "\033[92m"
            elif workflow.get_status() == Workflow.STATUS_FAILED:
                pretty_str += "\033[91m"
            elif workflow.get_status() == Workflow.STATUS_ABORTED:
                pretty_str += "\033[91m"
            elif workflow.get_status() == Workflow.STATUS_RESETED:
                pretty_str += "\033[3m"
            pretty_str += workflow.get_status() + "\033[0m"
            pretty_str += "\t" + elapsed_time + "\t" + start_time + "\t" + end_time
            return pretty_str
    
    def get_errors(self):
        if os.path.isfile(self.stderr):
            error = {
                "title"     : "",
                "msg"       : list(),
                "traceback" : list()
            }
            line_idx = 0
            FH_stderr = open( self.stderr )
            lines = FH_stderr.readlines()
            while line_idx < len(lines):
                if lines[line_idx].strip().startswith("##"):
                    error["title"]     = lines[line_idx].rstrip()
                    error["msg"]       = list()
                    error["traceback"] = list()
                    # skip all lines before the traceback
                    while not lines[line_idx].startswith("Traceback"):
                        line_idx += 1
                    # skip : "Traceback (most recent call last):"
                    line_idx += 1    
                    while lines[line_idx] != lines[line_idx].lstrip():
                        error["traceback"].append({ 
                                                   "location" : lines[line_idx].strip(),
                                                   "line"     : lines[line_idx].strip()
                        })
                        line_idx += 2
                    # Error message
                    while line_idx < len(lines) and not lines[line_idx].strip().startswith("##"):
                        try:
                            error["msg"].append( lines[line_idx].strip().split(":", 1)[1][1:] )
                        except:
                            error["msg"].append( lines[line_idx].strip() )
                        line_idx += 1
                    line_idx -= 1
                line_idx += 1
            FH_stderr.close()
            last_stack_location = ""
            if len(error["traceback"]) > 0:
                last_stack_location = error["traceback"][-1]["location"].strip()
                return { "msg" : error["msg"], "location" : last_stack_location }
            else:
                return None
        else:
            return None
                
    def get_outputs_per_components(self):
        outputs_files = {}
        for current_components in self.components:
            #status = self.get_component_status(current_components.get_nameid())
            outputs_files[current_components.get_nameid()] = current_components.get_output_files()
            #outputs_files["0"] = status["completed"]
        return outputs_files
    
    def __setstate__(self, state):
        self.__dict__ = state.copy()
        self.external_components = self._import_external_components()
        threading.Thread.__init__(self, name=self.name)
        
    def __getstate__(self):
        """
        Threading uses Lock Object, do not consider these objects when serializing a workflow
        """
        odict = self.__dict__.copy()
        del odict['_started']
        if '_tstate_lock' in odict: # python 3.4
            del odict['_tstate_lock']
        else: # python 3.2
            del odict['_block']
        del odict['_stderr']
        if 'external_components' in odict:
            del odict['external_components']
        return odict
    
    def set_to_address(self, to_address):
        self.__to_address = to_address

    def set_subject(self, subject):
        self.__subject = subject

    def set_message(self, message):
        self.__message = message

    def _get_cleaned_email_placeholders(self, text):
        """
        @summary: Returns the text after replacement of placeholders by the corresponding workflow values (method or attribute).
                  Placeholders must be an attribute or a method of the workflow between three sharps: ###attribute### or ###method()###.
                  You can add "|date" after the attribute or the method to convert a timestamp in human readable date.
                  Examples: ###id### is replaced by wf.id ; ###get_status()### is replaced by wf.get_status() ; ###start_time|date### is rplaced by wf.start_time in date format.
        @param text: [str] The text containing placeholders.
        @return: [str] The text with placeholders replaced by her real value.
        """
        new_text = text
        placeholders = re.findall("\#\#\#([^\#]+)\#\#\#", text)
        for placeholder in placeholders:
            try:
                placeholder_value = ""
                placeholder_key = placeholder
                is_date = False
                if placeholder.endswith("|date"):
                    placeholder_key = placeholder[:-5]
                    is_date = True
                # Get value
                if placeholder_key.endswith("()"):
                    placeholder_value = str(getattr(self, placeholder_key[:-2])())
                else:
                    placeholder_value = str(getattr(self, placeholder_key))
                # Apply date format
                if is_date:
                    jflow_date_format = self.jflow_config_reader.get_date_format()
                    placeholder_value = time.strftime(jflow_date_format + " %H:%M:%S", time.gmtime(float(placeholder_value)))
                new_text = new_text.replace("###" + placeholder + "###", placeholder_value)
            except:
                pass
        return new_text

    def _send_email(self):
        import smtplib
        from email.mime.text import MIMEText
        smtps, smtpp, froma, fromp, toa, subject, message = self.jflow_config_reader.get_email_options()
        
        if self.__to_address: toa = self.__to_address
        if self.__subject: subject = self.__subject
        if self.__message: message = self.__message
        
        if smtps and smtpp and froma and fromp:
            if not toa: toa = froma
            if validate_email(froma) and validate_email(toa):
                try:
                    # Open a plain text file for reading.  For this example, assume that
                    # the text file contains only ASCII characters.
                    # Create a text/plain message
                    if not message:
                        message = Workflow.get_status_under_text_format(self, True, True, True)
                    message = self._get_cleaned_email_placeholders( message )
                    msg = MIMEText(message, 'html')
                    me = froma
                    you = toa
                    if not subject:
                        subject = "JFlow - Workflow #" + str(self.id) + " is " + self.get_status()
                    subject = self._get_cleaned_email_placeholders( subject )
                    msg['Subject'] = subject
                    msg['From'] = me
                    msg['To'] = you
                    # Send the message via our own SMTP server, but don't include the
                    # envelope header.
                    s = smtplib.SMTP(smtps, smtpp)
                    s.ehlo()
                    # if the SMTP server does not provides TLS or identification
                    try:
                        s.starttls()
                        s.login(me, fromp)
                    except smtplib.SMTPHeloError:
                        self._log("The server didn't reply properly to the HELO greeting.", level="warning", traceback=traceback.format_exc(chain=False))
                    except smtplib.SMTPAuthenticationError:
                        self._log("The server didn't accept the username/password combination.", level="warning", traceback=traceback.format_exc(chain=False))
                    except smtplib.SMTPException:
                        self._log("No suitable authentication method was found, or the server does not support the STARTTLS extension.", level="warning", traceback=traceback.format_exc(chain=False))
                    except RuntimeError:
                        self._log("SSL/TLS support is not available to your Python interpreter.", level="warning", traceback=traceback.format_exc(chain=False))
                    except:
                        self._log("Unhandled error when sending mail.", level="warning", traceback=traceback.format_exc(chain=False))
                    finally:
                        s.sendmail(me, [you], msg.as_string())
                        s.close()
                except:
                    self._log("Impossible to connect to smtp server '" + smtps + "'", level="warning", traceback=traceback.format_exc(chain=False))
    
    def get_parameters_per_groups(self):
        name = self.get_name()
        description = self.get_description()
        parameters = self.get_parameters()
        pgparameters, parameters_order = {}, []
        for param in parameters:
            if param.group not in parameters_order: parameters_order.append(param.group)
            if param.group in pgparameters:
                pgparameters[param.group].append(param)
            else:
                pgparameters[param.group] = [param]
        return [pgparameters, parameters_order]
    
    def get_parameters(self):
        params = []
        for param in self.params_order:
            for attribute_value in list(self.__dict__.values()):
                if (issubclass(attribute_value.__class__, AbstractParameter)) and param == attribute_value.name:
                    params.append(attribute_value)
        return params
    
    def get_exec_path(self, software):
        exec_path = self.jflow_config_reader.get_exec(software)
        if exec_path is None and os.path.isfile(os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "../bin", software)):
            exec_path = os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "../bin", software)
        elif exec_path is None and os.path.isfile(os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "bin", software)):
            exec_path = os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "bin", software)
        elif exec_path is None and utils.which(software) == None:
            raise Exception("'" + software + "' path connot be retrieved either in the PATH and in the application.properties file!")
        elif exec_path is None and utils.which(software) != None: 
            exec_path = software
        elif exec_path != None and not os.path.isfile(exec_path):
            raise Exception("'" + exec_path + "' set for '" + software + "' does not exists, please provide a valid path!")
        return exec_path
    
    def add_component(self, component_name, args=[], kwargs={}, component_prefix="default"):
        # first build and check if this component is OK
        if component_name in self.internal_components or component_name in self.external_components:
            
            if component_name in self.internal_components:
                my_pckge = __import__(self.internal_components[component_name], globals(), locals(), [component_name])
                # build the object and define required field
                cmpt_object = getattr(my_pckge, component_name)()
                cmpt_object.output_directory = self.get_component_output_directory(component_name, component_prefix)
                cmpt_object.prefix = component_prefix
                if kwargs: cmpt_object.define_parameters(**kwargs)
                else: cmpt_object.define_parameters(*args)
            # external components
            else :
                cmpt_object = self.external_components[component_name]()
                cmpt_object.output_directory = self.get_component_output_directory(component_name, component_prefix)
                cmpt_object.prefix = component_prefix
                # can't use positional arguments with external components
                cmpt_object.define_parameters(**kwargs)
            
            # there is a dynamic component
            if cmpt_object.is_dynamic():
                self.dynamic_component_present = True
                # if already init, add the component to the list and check if weaver should be executed
                if self.component_nameids_is_init:
                    # add the component
                    self.components_to_exec.append(cmpt_object)
                    self.components.append(cmpt_object)
                    self._execute_weaver()
                    # update outputs
                    for output in cmpt_object.get_dynamic_outputs():
                        output.update()
                else:
                    if self._component_is_duplicated(cmpt_object):
                        raise ValueError("Component " + cmpt_object.__class__.__name__ + " with prefix " + 
                                            cmpt_object.prefix + " already exist in this pipeline!")
                    self.component_nameids[cmpt_object.get_nameid()] = None
                    self.components_to_exec = []
                    self.components = []
            else:
                if self.component_nameids_is_init:
                    # add the component
                    self.components_to_exec.append(cmpt_object)
                    self.components.append(cmpt_object)
                elif not self.component_nameids_is_init and not self.dynamic_component_present:
                    if self._component_is_duplicated(cmpt_object):
                        raise ValueError("Component " + cmpt_object.__class__.__name__ + " with prefix " + 
                                            cmpt_object.prefix + " already exist in this pipeline!")
                    self.components_to_exec.append(cmpt_object)
                    self.components.append(cmpt_object)
                else:
                    if self._component_is_duplicated(cmpt_object):
                        raise ValueError("Component " + cmpt_object.__class__.__name__ + " with prefix " + 
                                            cmpt_object.prefix + " already exist in this pipeline!")
                    self.component_nameids[cmpt_object.get_nameid()] = None

            return cmpt_object
        else:
            raise ImportError(component_name + " component cannot be loaded, available components are: {0}".format(
                                           ", ".join(list(self.internal_components.keys()) + list(self.external_components.keys()))))
    
    def pre_process(self):
        pass
    
    def process(self):
        """ 
        Run the workflow, has to be implemented by subclasses
        """
        raise NotImplementedError( "Workflow.process() must be implemented in " + self.__class__.__name__ )

    def get_name(self):
        """ 
        Return the workflow name.
        """
        return self.__class__.__name__.lower()
    
    def get_description(self):
        """ 
        Return the workflow description, has to be implemented by subclasses
        """
        raise NotImplementedError( "Workflow.get_description() must be implemented in " + self.__class__.__name__ )
    
    def define_parameters(self, function="process"):
        """ 
        Define the workflow parameters, has to be implemented by subclasses
        """
        raise NotImplementedError( "Workflow.define_parameters() must be implemented in " + self.__class__.__name__ )
    
    def post_process(self):
        pass
    
    def get_temporary_file(self, suffix=".txt"):
        tempfile_name = os.path.basename(tempfile.NamedTemporaryFile(suffix=suffix).name)
        return os.path.join(self.jflow_config_reader.get_tmp_directory(), tempfile_name)

    def get_component_output_directory(self, component_name, component_prefix):
        return os.path.join(self.directory, component_name + "_" + component_prefix)
    
    def get_components_nameid(self):
        return list(self.component_nameids.keys())
    
    def wf_execution_wrapper(self):
        getattr(self, self.function)()
    
    def run(self):
        """
        Only require for Threading
        """
        try:
            # if this is the first time the workflow run
            if self.__step == None:
                self.start_time = time.time()
                self.__step = 0
                self._status = self.STATUS_STARTED
                self._postprocess_status = self.STATUS_PENDING
                self.end_time = None
                # if some args are provided, let's fill the parameters
                self._set_parameters(self.args)
                self._serialize()
            # if pre_processing has not been done yet
            if self.__step == 0:
                self.pre_process()
                self.__step = 1
                self._serialize()
            # if collecting components and running workflow has not been done yet
            if self.__step == 1:
                self.reseted_components = []
                self.components = []
                self._status = self.STATUS_STARTED
                self._postprocess_status = self.STATUS_PENDING
                self._serialize()
                self.wf_execution_wrapper()
                self.component_nameids_is_init = True
                if self.dynamic_component_present:
                    self.__step = 2
                else:
                    self._execute_weaver()
                    self.__step = 3
                self._serialize()
            # if the workflow was a dynamic one
            if self.__step == 2:
                self.reseted_components = []
                self.components = []
                self._status = self.STATUS_STARTED
                self._postprocess_status = self.STATUS_PENDING
                self._serialize()
                self.wf_execution_wrapper()
                if len(self.components_to_exec) > 0:
                    self._execute_weaver()
                self.__step = 3
                self._serialize()
            # if post processing has ne been done yet
            if self.__step == 3:
                try:
                    self._postprocess_status = self.STATUS_STARTED
                    self.post_process()
                    self._postprocess_status = self.STATUS_COMPLETED
                    self._status = self.STATUS_COMPLETED
                except:
                    self._postprocess_status = self.STATUS_FAILED
                    raise
                self.end_time = time.time()
                self._serialize()

        except Exception as e:
            self._status = self.STATUS_FAILED
            self.end_time = time.time()
            if self.__step is not None:
                self._serialize()
            self._log(str(e), traceback=traceback.format_exc(chain=False))
            utils.display_error_message(str(e))
        finally:
            if self.__step is not None:
                self._send_email()

    def restart(self):
        """
        @summary: Reruns incompleted steps.
        @note: This method is asynchrone.
        """
        if hasattr(self, "stderr"):
            self._set_stderr()
        self._status = self.STATUS_STARTED
        self._postprocess_status = self.STATUS_PENDING
        self.start()

    def get_status(self):
        """
        @summary: Updates and returns self._status.
        @return: [STATUS] the workflow status.
        """
        try:
            working_directory = os.path.join(self.directory, self.WORKING)
            make_states = []
            for wdir in os.listdir(working_directory):
                log_path = os.path.join(working_directory, wdir, self.MAKEFLOW_LOG_FILE_NAME)
                log = MakeflowLog(log_path)
                log.parse()
                make_states.append(log.state)
            if len(self.reseted_components) > 0:
                self._status = self.STATUS_RESETED
            elif self.STATUS_ABORTED in make_states: # Error in component execution
                self._status = self.STATUS_ABORTED
            elif self.STATUS_FAILED in make_states: # Error in component execution
                self._status = self.STATUS_FAILED
            elif self._postprocess_status == self.STATUS_FAILED: # Error in postprocess
                self._status = self.STATUS_FAILED
        except: pass
        return self._status
    
    def get_resource(self, resource):
        return self.jflow_config_reader.get_resource(resource)
    
    def get_components_status(self):
        """
        @summary: Returns the components status for all components.
        @return: [dict] The components status by component name id.
        """
        status = dict()
        makeflows_logs = list() # Workflows with dynamic component(s) have several makeflows_logs
        for cmpt_nameid in self.get_components_nameid():
            status[cmpt_nameid] = {"time": 0.0,
                  "tasks": 0,
                  "waiting": 0,
                  "running": 0,
                  "failed": 0,
                  "aborted": 0,
                  "completed": 0,
                  "failed_commands": list() }
            if cmpt_nameid not in self.reseted_components:
                if self.component_nameids[cmpt_nameid] not in makeflows_logs:
                    makeflows_logs.append(self.component_nameids[cmpt_nameid])
        for current_makeflow_log in makeflows_logs:
            try:
                log = MakeflowLog(current_makeflow_log)
                log.parse()
                symbols = set(n.symbol for n in log.nodes if n.symbol)
                if not symbols: return None
                for n in log.nodes:
                    if not n.symbol: continue
                    cmpt_nameid = n.symbol.replace('"', '')
                    if cmpt_nameid in self.component_nameids and cmpt_nameid not in self.reseted_components:
                        status[cmpt_nameid]["tasks"] += 1
                        status[cmpt_nameid]["time"]  += n.elapsed_time
                        if n.state == Node.WAITING:
                            status[cmpt_nameid]["waiting"] += 1
                        elif n.state == Node.RUNNING:
                            status[cmpt_nameid]["running"] += 1
                        elif n.state == Node.FAILED:
                            status[cmpt_nameid]["failed"] += 1
                            status[cmpt_nameid]["failed_commands"].append( n.command )
                        elif n.state == Node.ABORTED:
                            status[cmpt_nameid]["aborted"] += 1
                        elif n.state == Node.COMPLETED:
                            status[cmpt_nameid]["completed"] += 1
            except: pass
        return status
    
    def get_component_status(self, component_nameid):
        return self.get_components_status()[component_nameid]
    
    def reset_component(self, component_name):
        # first reinit the step to the execution step
        self.__step = 1
        found = False
        for cpt in self.components:
            if cpt.get_nameid() == component_name:
                cpt.reset()
                found = True
        if not found:
            raise Exception("Impossible to reset component '" + component_name + "'! This one is not part of the workflow!")
        self.reseted_components.append(component_name)
        self._status = self.STATUS_RESETED
        self._serialize()
    
    def minimize(self):
        compts_status = self.get_components_status()
        return MINIWorkflow(self.id, self.name, self.description, self.get_status(), self.start_time, 
                            self.end_time, self.metadata, self.get_components_nameid(), compts_status, 
                            self.get_errors())
    
    def makeflow_pretty_print_node(self, dag, node):
        sys.stdout.write('{0:>10} {1} {2}\n'.format('NODE', node.id, node.symbol))
        
        for output_file in sorted(node.output_files):
            sys.stdout.write('{0:>10} {1:>10} {2}\n'.format('', 'OUTPUT', output_file))
    
        for input_file in sorted(node.input_files):
            sys.stdout.write('{0:>10} {1:>10} {2}\n'.format('', 'INPUT', input_file))
            
        sys.stdout.write('{0:>10} {1:>10} {2}\n'.format('', 'COMMAND', node.command))

    def _set_stderr(self):
        if hasattr(self, "stderr") and self.stderr is not None and os.path.isfile(self.stderr):
            os.rename( self.stderr, os.path.join(self.directory, str(time.time()) + "_" + self.STDERR_FILE_NAME + self.OLD_EXTENSION) )
        stderr = os.path.join(self.directory, self.STDERR_FILE_NAME)
        return stderr

    def _log(self, msg, level="exception", raisee=False, traceback=None):
        
        if level == "exception":
            logging.getLogger("wf." + str(self.id)).exception(msg)
            logh = open(self.stderr, "a")
            today = ddate.today()
            logh.write("## " + today.strftime("%c") + " :: " + msg + "\n")
            if traceback: logh.write(traceback)
            logh.close()
        elif level == "debug":
            logging.getLogger("wf." + str(self.id)).debug(msg)
        elif level == "warning":
            logging.getLogger("wf." + str(self.id)).warning(msg)
        
        if raisee:
            raise Exception(msg)

    def _execute_weaver(self, engine_wrapper=None):
        # Add nest path and path to script to Python module path to allow
        # for importing modules outside of $PYTHONPATH
        make_directory, new_make = self._get_current_make()
        current_working_directory = os.path.join(os.path.join(self.directory, self.WORKING), make_directory)
        sys.path.insert(0, os.path.abspath(os.path.dirname(current_working_directory)))

        # Load built-ins
        self._import('abstraction', ABSTRACTIONS)
        self._import('dataset', DATASETS)
        self._import('function', FUNCTIONS)
        self._import('nest', NESTS)
        self._import('options', OPTIONS)
        self._import('stack', STACKS)
                
        # Execute nest
        with Nest(current_working_directory, wrapper=engine_wrapper, path=self.jflow_config_reader.get_makeflow_path()) as nest:
            with self.options:
                if new_make:
                    try:
                        for component in self.components_to_exec:
                            nest.symbol = component.get_nameid()
                            nest.batch = component.batch_options
                            self.component_nameids[component.get_nameid()] = os.path.join(current_working_directory, self.MAKEFLOW_LOG_FILE_NAME)
                            component.execute()
                        # create the DAG
                        nest.compile()
                    except Exception as e:
                        self._status = self.STATUS_FAILED
                        self.end_time = time.time()
                        self._serialize()
                        raise
                self.components_to_exec = []
                # Once a weaver script is compiled, serialize the workflow
                self._serialize()
                try:
                    nest.execute(self.engine_arguments, exit_on_failure=True)
                    # close dag_file after execution to avoid nfs troubles
                    nest.dag_file.close()
                except:
                    self._status = self.STATUS_FAILED
                    self.end_time = time.time()
                    self._serialize()
                    raise

    def _get_current_make(self):
        current_component, make_directory, new_make = [], None, False
        for component in self.components_to_exec:
            current_component.append(component.get_nameid())
        for make in self.makes:
            if set(current_component) == set(self.makes[make]):
                make_directory = make
        # If the components in the queue have already been compiled
        if make_directory is None:
            make_directory = uuid.uuid4().hex[:10]
            self.makes[make_directory] = current_component
            new_make = True
        return [make_directory, new_make]
    
    def _serialize(self):
        self.dump_path = os.path.join(self.directory, self.DUMP_FILE_NAME)
        workflow_dump = open(self.dump_path, "wb")
        pickle.dump(self, workflow_dump)
        workflow_dump.close()

    def _component_is_duplicated(self, component):
        if component.get_nameid() in list(self.component_nameids.keys()):
            return True
        return False

    def _import_internal_components(self):
        pckge = {}
        # then import pipeline packages
        pipeline_dir = os.path.dirname(inspect.getfile(self.__class__))
        for importer, modname, ispkg in pkgutil.iter_modules([os.path.join(pipeline_dir, "components")], "workflows." + 
                                                             os.path.basename(pipeline_dir) + ".components."):
            try:
                m = __import__(modname)
                for class_name, obj in inspect.getmembers(sys.modules[modname], inspect.isclass):
                    if issubclass(obj, jflow.component.Component) and obj.__name__ != jflow.component.Component.__name__:
                        pckge[class_name] = modname
            except Exception as e:
                self._log("Component <{0}> cannot be loaded: {1}".format(modname, e), level="debug", traceback=traceback.format_exc(chain=False))
        # finally import workflows shared packages
        workflows_dir = os.path.dirname(os.path.dirname(inspect.getfile(self.__class__)))
        for importer, modname, ispkg in pkgutil.iter_modules([os.path.join(workflows_dir, "components")], "workflows.components."):
            try:
                m = __import__(modname)
                for class_name, obj in inspect.getmembers(sys.modules[modname], inspect.isclass):
                    if issubclass(obj, jflow.component.Component) and obj.__name__ != jflow.component.Component.__name__:
                        pckge[class_name] = modname
            except Exception as e:
                self._log("Component <{0}> cannot be loaded: {1}".format(modname, e), level="debug", traceback=traceback.format_exc(chain=False))
        return pckge
    
    def _import_external_components(self):
        pckge = {}
        parsers = []
        # get exparsers
        extparsers_dir = os.path.join( os.path.dirname(os.path.dirname(inspect.getfile(self.__class__))), 'extparsers' )
        for importer, modname, ispkg in pkgutil.iter_modules([extparsers_dir], "workflows.extparsers.") :
            try :
                m = __import__(modname)
                for class_name, obj in inspect.getmembers(sys.modules[modname], inspect.isclass):
                    if issubclass(obj, jflow.extparser.ExternalParser) and obj.__name__ != jflow.extparser.ExternalParser.__name__:
                        parsers.append(obj())
            except Exception as e:
                self._log("Parser <{0}> cannot be loaded: {1}".format(modname, e), level="debug", traceback=traceback.format_exc(chain=False))
        
        for parser in parsers :
            # import from pipeline components package ...
            pipeline_components_dir = os.path.join( os.path.dirname(inspect.getfile(self.__class__)), "components" )
            
            # ... and from shared components package
            workflow_components_dir = os.path.join(os.path.dirname(os.path.dirname(inspect.getfile(self.__class__))), "components" )
            
            try :
                comps = parser.parse_directory(pipeline_components_dir) + parser.parse_directory(workflow_components_dir)
                for c in comps :
                    pckge[c.__name__] = c
            except :
                pass
        return pckge
        
    def _import(self, module, symbols):
        """ Import ``symbols`` from ``module`` into global namespace. """
        # Import module
        m = 'weaver.{0}'.format(module)
        m = __import__(m, self.globals, self.globals, symbols)

        # Import symbols from module into global namespace, which we store as
        # an attribute for later use (i.e. during compile)
        for symbol in symbols:
            self.globals[symbol] = getattr(m, symbol)