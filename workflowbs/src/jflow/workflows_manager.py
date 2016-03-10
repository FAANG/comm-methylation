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

import pkgutil
import workflows
import inspect
import jflow
import sys
import imp
import os
import pickle
import threading
import logging

import jflow.utils as utils
import jflow.concurrent_access as concurrent
from jflow.config_reader import JFlowConfigReader

class WorkflowsManager(object):

    IDS_FILE_NAME = "jflowIDs.txt"
    WORKFLOWS_DUMP_FILE_NAME = ".workflows.dump"
    WF_DIRECTORY_PREFIX = "wf"

    def __init__(self):
        self.config_reader = JFlowConfigReader()
        if not os.path.isdir(self.get_output_directory()):
            os.makedirs(self.get_output_directory(), 0o751)
        self.dump_file = os.path.join(self.get_output_directory(), self.WORKFLOWS_DUMP_FILE_NAME)
        self.ids_file = os.path.join(self.get_output_directory(), self.IDS_FILE_NAME)
    
    def _dump_workflows(self, workflows):
        def dump_func():
            # first load the existing workflows
            try:
                wdfh = open(self.dump_file, "rb")
                workflows_dump = pickle.load(wdfh)
                wdfh.close()
            except:
                workflows_dump = {}
            # then add the new ones
            for workflow in workflows:
                workflows_dump[utils.get_nb_string(workflow.id)] = {"dump_path": workflow.dump_path,
                                                                    "object": workflow.minimize()}
            # and save them
            wdfh = open(self.dump_file, "wb")
            pickle.dump(workflows_dump, wdfh)
            wdfh.close()
        workflows_ids = [wf.id for wf in workflows]
        concurrent.exec_on_shared( dump_func, self.dump_file, self.config_reader.get_tmp_directory(), 1, 200, {"action": "Add wf", "wf_id": workflows_ids} )

    def get_available_workflows(self, function="process", filter_groups = [], select = False ):
        if function.__class__.__name__ == "str":
            functions = [function]
        else:
            functions = set(function)
        wf_instances, wf_methodes = [], []
        
        if isinstance(filter_groups, str): filter_groups = [filter_groups]
        
        # Load all modules within the workflow module
        for importer, modname, ispkg in pkgutil.iter_modules(workflows.__path__, workflows.__name__ + "."):
            __import__(modname)
            # Search for Workflow classes
            for class_name, obj in inspect.getmembers(sys.modules[modname], inspect.isclass):
                if issubclass(obj, jflow.workflow.Workflow) and obj.__name__ != jflow.workflow.Workflow.__name__:
                    for function in functions:
                        # check if the workflow has the requested methode
                        # inspect.ismethod has been changed for inspect.isfunction in Python3
                        for ifunction in inspect.getmembers(obj, predicate=inspect.isfunction):    
                            if ifunction[0] == function:
                                # try to build the workflow
                                try: 
                                    select_workflow = True
                                    inst = obj(function=function)
                                    if filter_groups :
                                        select_workflow = (inst.get_workflow_group() in filter_groups) == select
                                    
                                    if select_workflow: 
                                        wf_instances.append(inst)
                                        wf_methodes.append(function)
                                except: pass
        return [wf_instances, wf_methodes]
    
    def rerun_workflow(self, workflow_id):
        workflow = self.get_workflow(workflow_id)
        workflow.restart()
        # Update the workflow in the cache
        self._dump_workflows([workflow])
        return workflow

    def reset_workflow_component(self, workflow_id, component_name):
        workflow = self.get_workflow(workflow_id)
        workflow.reset_component(component_name)
        # Update the workflow in the cache
        self._dump_workflows([workflow])
        return workflow
    
    def run_workflow(self, workflow_class, args, function="process"):
        # Load all modules within the workflow module
        for importer, modname, ispkg in pkgutil.iter_modules(workflows.__path__, workflows.__name__ + "."):
            __import__(modname)
            # Search for Workflow classes
            for class_name, obj in inspect.getmembers(sys.modules[modname], inspect.isclass):
                if class_name == workflow_class: workflow = obj(args, self.get_next_id(), function)
        workflow.start()
        # Add the workflow dump path to the workflows dump
        self._dump_workflows([workflow])
        return workflow

    def delete_workflow(self, workflow_id):
        from jflow.workflow import Workflow
        def delete_func():
            try:
                awfh = open(self.dump_file, "rb")
                all_workflows_dump = pickle.load(awfh)
                awfh.close()
            except:
                all_workflows_dump = {}
            rworkflow_id = utils.get_nb_string(workflow_id)
            try:
                workflow_dump = open(all_workflows_dump[rworkflow_id]["dump_path"], "rb")
                workflow = pickle.load(workflow_dump)
                workflow_dump.close()
                # if workflow is not in a running status
                if workflow.get_status() in [Workflow.STATUS_COMPLETED, Workflow.STATUS_FAILED, Workflow.STATUS_ABORTED]:
                    workflow.delete()
                    del all_workflows_dump[rworkflow_id]
            except:
                logging.getLogger("jflow").debug("Workflow #" + rworkflow_id + " connot be retrieved in the available workflows!")
                raise Exception("Workflow #" + rworkflow_id + " connot be retrieved in the available workflows!")
            # and save them
            awfh = open(self.dump_file, "wb")
            pickle.dump(all_workflows_dump, awfh)
            awfh.close()
        concurrent.exec_on_shared( delete_func, self.dump_file, self.config_reader.get_tmp_directory(), 1, 200, {"action": "Delete wf", "wf_id": str(workflow_id)} )

    def get_workflow_errors(self, workflow_id):
        workflow = self.get_workflow(workflow_id)
        return workflow.get_errors()
    
    def get_output_directory(self):
        return self.config_reader.get_work_directory()
        
    def get_workflow_outputs(self, workflow_id):
        workflow = self.get_workflow(workflow_id)
        return workflow.get_outputs_per_components()
        
    def get_workflows(self, use_cache=False):
        from jflow.workflow import Workflow
        workflows = []
        try:
            awfh = open(self.dump_file, "rb")
            workflows_dump = pickle.load(awfh)
            awfh.close()
        except:
            workflows_dump = {}
        updated_workflows = []
        for workflow_id in workflows_dump:
            # is the workflow completed, failed or aborted use the miniworkflow cached
            if use_cache and workflows_dump[workflow_id]["object"].get_status() in [Workflow.STATUS_COMPLETED, Workflow.STATUS_FAILED, Workflow.STATUS_ABORTED]:
                workflows.append(workflows_dump[workflow_id]["object"])
            else:
                try:
                    workflow_dump = open(workflows_dump[workflow_id]["dump_path"], "rb")
                    workflow = pickle.load(workflow_dump)
                    workflows.append(workflow)
                    updated_workflows.append(workflow)
                    workflow_dump.close()
                except: pass
        self._dump_workflows(updated_workflows)
        return workflows

    def get_workflow_by_class(self, workflow_class):
        # Load all modules within the workflow module
        for importer, modname, ispkg in pkgutil.iter_modules(workflows.__path__, workflows.__name__ + "."):
            __import__(modname)
            # Search for Workflow classes
            for class_name, obj in inspect.getmembers(sys.modules[modname], inspect.isclass):
                if class_name == workflow_class:
                    return obj()
        return None
    
    def get_workflow(self, workflow_id):
        rworkflow_id = utils.get_nb_string(workflow_id)
        try:
            wdfh = open(self.dump_file, "rb")
            workflows_dump = pickle.load(wdfh)
            wdfh.close()
        except:
            workflows_dump = {}
        if rworkflow_id in workflows_dump:
            workflow_dump = open(workflows_dump[rworkflow_id]["dump_path"], "rb")
            workflow = pickle.load(workflow_dump)
            workflow_dump.close()
        else:
            logging.getLogger("jflow").debug("Workflow #" + str(rworkflow_id) + " connot be retrieved in the available workflows!")
            raise Exception("Workflow #" + str(rworkflow_id) + " connot be retrieved in the available workflows!")
        return workflow

    def get_workflow_directory(self, wname, wid):
        return os.path.join(os.path.join(self.config_reader.get_work_directory(), wname), 
                                         self.WF_DIRECTORY_PREFIX + utils.get_nb_string(wid))

    def get_next_id(self):
        def next_id_func():
            if os.path.isfile(self.ids_file):
                ifh = open(self.ids_file)
                cid = int(ifh.readline().strip())
                ifh.close()
                ifh = open(self.ids_file, "w")
                ifh.write(str(cid+1))
                ifh.close()
                return cid+1
            else:
                ifh = open(self.ids_file, "w")
                ifh.write("1")
                ifh.close()
                return 1
        return concurrent.exec_on_shared( next_id_func, self.ids_file, self.config_reader.get_tmp_directory(), metadata={"action": "Get wf ID"} )
