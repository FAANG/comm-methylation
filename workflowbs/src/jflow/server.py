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

import cherrypy
import cgi
import tempfile
import json
import sys
import datetime
from functools import wraps
import time
import os
import argparse

from argparse import ArgumentTypeError

from .workflows_manager import WorkflowsManager
from .config_reader import JFlowConfigReader
from .workflow import Workflow
from .parameter import browsefile, localfile, urlfile, inputfile, create_test_function, MiltipleAction, MiltipleAppendAction, MultipleParameters
from workflows.types import *
from . import utils
from cctools.util import time_format
from .utils import get_octet_string_representation

# function in charge to upload large files
class UploadFieldStorage(cgi.FieldStorage):
    """Our version uses a named temporary file instead of the default
    non-named file; keeping it visibile (named), allows us to create a
    2nd link after the upload is done, thus avoiding the overhead of
    making a copy to the destination filename."""

    def get_tmp_directory(self):
        jflowconf = JFlowConfigReader()
        return jflowconf.get_tmp_directory()

    def get_file_name(self):
        self.tmpfile = None
        # if this is a file object, just return the name of the file
        if hasattr( self.file, 'name' ):
            return self.file.name
        # if not, this is a cStringIO.StringO, write it down
        # and return the file name
        else:
            tmp_folder = self.get_tmp_directory()
            if not os.path.exists( tmp_folder ):
                try : os.mkdir(tmp_folder)
                except : pass
            fh = open(os.path.join(tmp_folder, self.filename), "wb+")
            fh_name = fh.name
            fh.write(self.file.getvalue())
            fh.close()
            return fh_name

    def __del__(self):
        try:
            self.file.close()
        except AttributeError:
            pass
        try:
            tmp_folder = self.get_tmp_directory()
            os.remove(os.path.join(tmp_folder, self.filename))
        except:
            pass

    def make_file(self, binary=None):
        tmp_folder = self.get_tmp_directory()
        if not os.path.exists( tmp_folder ):
            try : os.mkdir(tmp_folder)
            except : pass
        return tempfile.NamedTemporaryFile(dir=tmp_folder)


def noBodyProcess():
    """Sets cherrypy.request.process_request_body = False, giving
    us direct control of the file upload destination. By default
    cherrypy loads it to memory, we are directing it to disk."""
    cherrypy.request.process_request_body = False

cherrypy.tools.noBodyProcess = cherrypy.Tool('before_request_body', noBodyProcess)

# define functions in charge to handle cross domain calls
def CORS():
    cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
    cherrypy.response.headers['Access-Control-Allow-Methods'] = 'OPTIONS, GET, POST'
    cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Content-Range, Content-Disposition'
cherrypy.tools.CORS = cherrypy.Tool('before_finalize', CORS)

class JFlowJSONEncoder (json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.strftime( JFlowConfigReader().get_date_format() )
        else:
            return json.JSONEncoder.default(self, obj)

class JFlowServer (object):

    MULTIPLE_TYPE_SPLITER = "___"
    APPEND_PARAM_SPLITER = "::-::"
    JFLOW_WDATA = "data"

    def __init__(self):
        # Create a workflow manager to get access to our workflows
        self.wfmanager = WorkflowsManager()
        self.jflow_config_reader = JFlowConfigReader()
    
    @staticmethod
    def quickstart(server_class, config=None, daemon=False):
        
        # daemonize the server if asked to
        if daemon:
            from cherrypy.process.plugins import Daemonizer
            Daemonizer(cherrypy.engine).subscribe()
        
        # define the socket host and port
        jflowconf = JFlowConfigReader()
        socket_opts = jflowconf.get_socket_options()
        
        # add the result directory
        if config is None or not '/' in config:
            config['/'] = {'tools.staticdir.root': jflowconf.get_work_directory()}
        else:
            link = os.path.join(config['/']['tools.staticdir.root'], "data")
            if not os.path.islink(link):
                os.symlink(jflowconf.get_work_directory(), link)
            
        config[os.path.join('/', JFlowServer.JFLOW_WDATA)] = {'tools.staticdir.on'  : True,
                                                              'tools.staticdir.dir' : jflowconf.get_work_directory()}
    
        # remove any limit on the request body size; cherrypy's default is 100MB
        # (maybe we should just increase it ?)
        cherrypy.server.max_request_body_size = 0
    
        # increase server socket timeout to 60s; we are more tolerant of bad
        # quality client-server connections (cherrypy's default is 10s)
        cherrypy.server.socket_timeout = 60
    
        cherrypy.config.update({'server.socket_host': socket_opts[0],
                                'server.socket_port': socket_opts[1]})
        # start the server
        cherrypy.quickstart(server_class(), config=config)
    
    def jsonify(func):
        '''JSON and JSONP decorator for CherryPy'''
        @wraps(func)
        def wrapper(*args, **kw):
            value = func(*args, **kw)
            cherrypy.response.headers["Content-Type"] = "application/json"
            # if JSONP request
            if "callback" in kw: 
                return ('%s(%s)' % (kw["callback"], json.dumps(value, cls=JFlowJSONEncoder))).encode('utf8')
            # else return the JSON
            else: return json.dumps(value, cls=JFlowJSONEncoder).encode('utf8')
        return wrapper

    def jsonify_workflow_status(self, workflow, init_to_zero=False):
        if workflow.start_time: start_time = time.asctime(time.localtime(workflow.start_time))
        else: start_time = "-"
        if workflow.start_time and workflow.end_time: elapsed_time = str(workflow.end_time-workflow.start_time)
        elif workflow.start_time: elapsed_time = str(time.time()-workflow.start_time)
        else: elapsed_time = "-"
        if workflow.end_time: end_time = time.asctime(time.localtime(workflow.end_time))
        else: end_time = "-"
        if init_to_zero:
            return {"id":utils.get_nb_string(workflow.id),
                    "name": workflow.name,
                    "status": Workflow.STATUS_STARTED,
                    "elapsed_time": str(elapsed_time),
                    "start_time": start_time,
                    "end_time": end_time,
                    "components": []}
        else:
            components = []
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
                components.append({"name": component,
                                  "elapsed_time": time_format(status_info["time"]),
                                  "total": status_info["tasks"],
                                  "waiting": status_info["waiting"],
                                  "failed": status_info["failed"],
                                  "running": status_info["running"],
                                  "aborted": status_info["aborted"],
                                  "completed": status_info["completed"]})

            status = {"id":utils.get_nb_string(workflow.id),
                      "errors": workflow.get_errors(),
                      "name": workflow.name,
                      "metadata": workflow.metadata,
                      "status": workflow.get_status(),
                      "elapsed_time": "-" if elapsed_time == "-" else str(datetime.timedelta(seconds=int(str(elapsed_time).split(".")[0]))),
                      "start_time": start_time,
                      "end_time": end_time,
                      "components": components}

            return status

    @cherrypy.expose
    @jsonify
    def get_available_workflows(self, **kwargs):
        workflows = []
        filter_groups = None
        select = False
        if 'filter_groups' in kwargs : filter_groups = kwargs['filter_groups'].split(',')
        if 'select' in kwargs : select = kwargs['select'] in ['True', 'true', '1', 1]

        wf_instances, wf_methodes = self.wfmanager.get_available_workflows(filter_groups = filter_groups  , select = select)
        for instance in wf_instances:
            parameters, parameters_per_groups, ordered_groups = [], {}, ["default"]
            for param in instance.get_parameters():
                # if it's a multiple action change the action by the name
                if param.action == MiltipleAction:
                    action = "MiltipleAction"
                elif param.action == MiltipleAppendAction:
                    action = "MiltipleAppendAction"
                else:
                    action = param.action
                try:
                    cparam_help = param.global_help
                except:
                    cparam_help = param.help
                hash_param = {"help": cparam_help,
                              "required": param.required,
                              "default": param.default,
                              "choices": param.choices,
                              "action": action,
                              "type": param.get_type(),
                              "name": param.name,
                              "display_name": param.display_name,
                              "group": param.group}
                if hash_param["type"] == "date":
                    hash_param["format"] = self.jflow_config_reader.get_date_format()
                    if hash_param["format"] == '%d/%m/%Y':
                        hash_param["format"] = 'dd/mm/yyyy'
                    elif hash_param["format"] == '%d/%m/%y':
                        hash_param["format"] = 'dd/mm/yy'
                    elif hash_param["format"] == '%Y/%m/%d':
                        hash_param["format"] = 'yyyy/mm/dd'
                    elif hash_param["format"] == '%y/%m/%d':
                        hash_param["format"] = 'yy/mm/dd'
                # if it's a multiple type add sub parameters
                if type(param.type) == MultipleParameters:
                    hash_param["sub_parameters"] = []
                    for sub_param in param.sub_parameters:
                        hash_param["sub_parameters"].append({"help": sub_param.help,
                              "required": sub_param.required,
                              "default": sub_param.default,
                              "choices": sub_param.choices,
                              "action": sub_param.action,
                              "type": sub_param.get_type(),
                              "name": param.name + JFlowServer.MULTIPLE_TYPE_SPLITER + sub_param.flag,
                              "display_name": sub_param.display_name,
                              "group": sub_param.group})
                        if hash_param["sub_parameters"][-1]["type"] == "date":
                            hash_param["sub_parameters"][-1]["format"] = self.jflow_config_reader.get_date_format()
                            if hash_param["sub_parameters"][-1]["format"] == '%d/%m/%Y':
                                hash_param["sub_parameters"][-1]["format"] = 'dd/mm/yyyy'
                            elif hash_param["sub_parameters"][-1]["format"] == '%d/%m/%y':
                                hash_param["sub_parameters"][-1]["format"] = 'dd/mm/yy'
                            elif hash_param["sub_parameters"][-1]["format"] == '%Y/%m/%d':
                                hash_param["sub_parameters"][-1]["format"] = 'yyyy/mm/dd'
                            elif hash_param["sub_parameters"][-1]["format"] == '%y/%m/%d':
                                hash_param["sub_parameters"][-1]["format"] = 'yy/mm/dd'
                parameters.append(hash_param)
                if param.group in parameters_per_groups:
                    parameters_per_groups[param.group].append(hash_param)
                else: parameters_per_groups[param.group] = [hash_param]
                if param.group not in ordered_groups:
                    ordered_groups.append(param.group)
            workflows.append({"name": instance.name,
                              "help": instance.description,
                              "class": instance.__class__.__name__,
                              "parameters": parameters,
                              "parameters_per_groups": parameters_per_groups,
                              "groups": ordered_groups})
        return workflows

    @cherrypy.expose
    @jsonify
    def run_workflow(self, **kwargs):
        try:
            kwargs_modified = {}

            # handle MultiParameterList
            multi_sub_params = {}
            for key in list(kwargs.keys()):
                parts = key.split(JFlowServer.MULTIPLE_TYPE_SPLITER)
                if len(parts) == 3:
                    if not parts[0] in kwargs_modified:
                        kwargs_modified[parts[0]] = []
                        multi_sub_params[parts[0]] = {}
                    if parts[2] in multi_sub_params[parts[0]]:
                        multi_sub_params[parts[0]][parts[2]].append((parts[1], kwargs[key]))
                    else:
                        multi_sub_params[parts[0]][parts[2]] = [(parts[1], kwargs[key])]

            for key in list(kwargs.keys()):
                parts = key.split(JFlowServer.MULTIPLE_TYPE_SPLITER)
                # split append values
                new_values = kwargs[key].split(JFlowServer.APPEND_PARAM_SPLITER)
                if len(new_values) == 1:
                    new_values = new_values[0]
                # if this is a classic Parameter
                if len(parts) == 1:
                    kwargs_modified[key] = new_values
                # if this is a MultiParameter
                elif len(parts) == 2:
                    if parts[0] in kwargs_modified:
                        kwargs_modified[parts[0]].append((parts[1], new_values))
                    else:
                        kwargs_modified[parts[0]] = [(parts[1], new_values)]

            # handle MultiParameterList
            for param in multi_sub_params:
                kwargs_modified[param] = []
                for sub_param in multi_sub_params[param]:
                    kwargs_modified[param].append(multi_sub_params[param][sub_param])

            workflow = self.wfmanager.run_workflow(kwargs_modified["workflow_class"], kwargs_modified)
            return { "status" : 0, "content" : self.jsonify_workflow_status(workflow, True) }
        except Exception as err:
            return { "status" : 1, "content" : str(err) }

    @cherrypy.expose
    @jsonify
    def delete_workflow(self, **kwargs):
        self.wfmanager.delete_workflow(kwargs["workflow_id"])

    @cherrypy.expose
    @jsonify
    def rerun_workflow(self, **kwargs):
        workflow = self.wfmanager.rerun_workflow(kwargs["workflow_id"])
        return self.jsonify_workflow_status(workflow)

    @cherrypy.expose
    @jsonify
    def reset_workflow_component(self, **kwargs):
        workflow = self.wfmanager.reset_workflow_component(kwargs["workflow_id"], kwargs["component_name"])
        return self.jsonify_workflow_status(workflow)

    @cherrypy.expose
    def upload_light(self, **kwargs):
        uniq_directory = ""
        for key in list(kwargs.keys()):
            if key == "uniq_directory":
                uniq_directory = kwargs['uniq_directory']
            else:
                file_param = key

        # the file transfer can take a long time; by default cherrypy
        # limits responses to 300s; we increase it to 1h
        cherrypy.response.timeout = 3600

        # upload file by chunks
        file_dir = os.path.join( self.jflow_config_reader.get_tmp_directory(), uniq_directory )
        os.mkdir( file_dir )

        if isinstance(kwargs[file_param], list):
            for cfile in kwargs[file_param]:
                FH_sever_file = open(os.path.join(file_dir, cfile.filename), "w")
                while True:
                    data = cfile.file.read(8192)
                    if not data:
                        break
                    FH_sever_file.write(data)
                FH_sever_file.close()
        else:
            FH_sever_file = open(os.path.join(file_dir, kwargs[file_param].filename), "w")
            while True:
                data = kwargs[file_param].file.read(8192)
                if not data:
                    break
                FH_sever_file.write(data)
            FH_sever_file.close()

    @cherrypy.expose
    @cherrypy.tools.noBodyProcess()
    @cherrypy.tools.CORS()
    def upload(self):
        # the file transfer can take a long time; by default cherrypy
        # limits responses to 300s; we increase it to 1h
        cherrypy.response.timeout = 3600

        # convert the header keys to lower case
        lcHDRS = {}
        for key, val in cherrypy.request.headers.items():
            lcHDRS[key.lower()] = val

        # at this point we could limit the upload on content-length...
        # incomingBytes = int(lcHDRS['content-length'])

        # create our version of cgi.FieldStorage to parse the MIME encoded
        # form data where the file is contained
        formFields = UploadFieldStorage(fp=cherrypy.request.rfile,
                                        headers=lcHDRS,
                                        environ={'REQUEST_METHOD':'POST'},
                                        keep_blank_values=True)

        # we now create a link to the file, using the submitted
        # filename; if we renamed, there would be a failure because
        # the NamedTemporaryFile, used by our version of cgi.FieldStorage,
        # explicitly deletes the original filename
        for current in list(formFields.keys()):
            if current != 'uniq_directory':
                currentFile = formFields[current]
                fileDir = os.path.join(self.jflow_config_reader.get_tmp_directory(), formFields.getvalue("uniq_directory"))
                os.mkdir(fileDir)
                if isinstance(currentFile, list):
                    for cfile in currentFile:
                        os.link(
                                cfile.get_file_name(),
                                os.path.join(fileDir, cfile.filename)
                        )
                else:
                    os.link(
                            currentFile.get_file_name(),
                            os.path.join(fileDir, currentFile.filename)
                    )

    @cherrypy.expose
    @jsonify
    def get_workflows_status(self, **kwargs):
        status = []
        workflows = self.wfmanager.get_workflows(use_cache=True)
        for workflow in workflows:
            if "metadata_filter" in kwargs:
                is_ok = False
                for wf_meta in workflow.metadata:
                    for metadata in kwargs["metadata_filter"].split(","):
                        if wf_meta == metadata:
                            is_ok = True
                            break
                    if is_ok: break
                if is_ok: status.append(self.jsonify_workflow_status(workflow))
            else:
                status.append(self.jsonify_workflow_status(workflow))
        return status

    @cherrypy.expose
    @jsonify
    def get_workflow_status(self, **kwargs):
        workflow = self.wfmanager.get_workflow(kwargs["workflow_id"])
        if kwargs["display"] == "list":
            return self.jsonify_workflow_status(workflow)
        elif kwargs["display"] == "graph":
            g = workflow.get_execution_graph()
            status = self.jsonify_workflow_status(workflow)
            nodes = []
            for node in g.nodes():
                if Workflow.INPUTFILE_GRAPH_LABEL in g.node_attributes(node):
                    nodes.append({"name": node, "display_name": g.node_attributes(node)[1], "type": "inputfile"})
                elif Workflow.INPUTFILES_GRAPH_LABEL in g.node_attributes(node):
                    nodes.append({"name": node, "display_name": g.node_attributes(node)[1], "type": "inputfiles"})
                elif Workflow.INPUTDIRECTORY_GRAPH_LABEL in g.node_attributes(node):
                    nodes.append({"name": node, "display_name": g.node_attributes(node)[1], "type": "inputdirectory"})    
                elif Workflow.COMPONENT_GRAPH_LABEL in g.node_attributes(node):
                    nodes.append({"name": node, "display_name": g.node_attributes(node)[1], "type": "component"})
            status["nodes"] = nodes
            status["edges"] = g.edges()
            return status

    def _webify_outputs(self, web_path, path):
        work_dir  = self.jflow_config_reader.get_work_directory()
        if work_dir.endswith("/"): work_dir = work_dir[:-1]
        socket_opt = self.jflow_config_reader.get_socket_options()
        return {
                'url':'http://' + socket_opt[0] + ':' + str(socket_opt[1]) + '/' + path.replace(work_dir, web_path),
                'size': get_octet_string_representation(os.path.getsize(os.path.abspath(path))),
                'extension': os.path.splitext(path)[1]
               }

    @cherrypy.expose
    @jsonify
    def get_workflow_outputs(self, **kwargs):
        on_disk_outputs, on_web_outputs = self.wfmanager.get_workflow_outputs(kwargs["workflow_id"]), {}
        for cpt_name in list(on_disk_outputs.keys()):
            on_web_outputs[cpt_name] = {}
            for outf in on_disk_outputs[cpt_name]:
                on_web_outputs[cpt_name][outf] = self._webify_outputs(JFlowServer.JFLOW_WDATA, on_disk_outputs[cpt_name][outf])
        return on_web_outputs

    @cherrypy.expose
    @jsonify
    def validate_field(self, **kwargs):
        try:
            value_key = None
            for key in list(kwargs.keys()):
                if key != "type" and key != "callback" and key != "_" and key != "action": 
                    value_key = key
                    break
            # if it's an append parameter, let's check each value
            if kwargs["action"] == "append":
                for cval in kwargs[value_key].split("\n"):
                    create_test_function(kwargs["type"])(cval)
            else:
                create_test_function(kwargs["type"])(kwargs[value_key])
            return True
        except Exception as e:
            return str(e)