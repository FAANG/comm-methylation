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

import sys
import argparse
import time

try:
    import _preamble
except ImportError:
    sys.exc_clear()

from jflow.workflows_manager import WorkflowsManager
from jflow.workflow import Workflow
import jflow.utils as utils

class JflowArgumentParser (argparse.ArgumentParser):
    def _read_args_from_files(self, arg_strings):
        # expand arguments referencing files
        new_arg_strings = []
        for arg_string in arg_strings:
            # if it's not a comment or an empty line
            if not arg_string.startswith("#") and arg_string:
                # for regular arguments, just add them back into the list
                if not arg_string or arg_string[0] not in self.fromfile_prefix_chars:
                    new_arg_strings.append(arg_string)
                # replace arguments referencing files with the file content
                else:
                    try:
                        with open(arg_string[1:]) as args_file:
                            arg_strings = []
                            # give to the convert_arg_line_to_args a table of lines instead of line per line
                            for arg in self.convert_arg_line_to_args(args_file.read().splitlines()):
                                arg_strings.append(arg)
                            arg_strings = self._read_args_from_files(arg_strings)
                            new_arg_strings.extend(arg_strings)
                    except OSError:
                        err = _sys.exc_info()[1]
                        self.error(str(err))
        # return the modified argument list
        return new_arg_strings


if __name__ == '__main__':

    # Create a workflow manager to get access to our workflows
    wfmanager = WorkflowsManager()
    
    # Create the top-level parser
    parser = JflowArgumentParser()
    subparsers = parser.add_subparsers(title='Available sub commands')
    
    # Add rerun workflow availability
    sub_parser = subparsers.add_parser("rerun", help="Rerun a specific workflow")
    sub_parser.add_argument("--workflow-id", type=str, help="Which workflow should be rerun",
                            required=True, dest="workflow_id")
    sub_parser.set_defaults(cmd_object="rerun")

    # Add rerun workflow availability
    sub_parser = subparsers.add_parser("reset", help="Reset a workflow component")
    sub_parser.add_argument("--workflow-id", type=str, help="Which workflow should be used",
                            required=True, dest="workflow_id")
    sub_parser.add_argument("--component-name", type=str, help="Which component should be reseted",
                            required=True, dest="component_name")
    sub_parser.set_defaults(cmd_object="reset")

    # Add delete workflow availability
    sub_parser = subparsers.add_parser("delete", help="Delete a workflow")
    sub_parser.add_argument("--workflow-id", type=str, help="Which workflow should be deleted",
                            required=True, dest="workflow_id")
    sub_parser.set_defaults(cmd_object="delete")

    # Add rerun workflow availability
    sub_parser = subparsers.add_parser("execution-graph", help="Display the workflow execution graph")
    sub_parser.add_argument("--workflow-id", type=str, help="Which workflow should be considered",
                            required=True, dest="workflow_id")
    sub_parser.set_defaults(cmd_object="execution_graph")

    # Add status workflow availability
    sub_parser = subparsers.add_parser("status", help="Monitor a specific workflow")
    sub_parser.add_argument("--workflow-id", type=str, help="Which workflow status should be displayed",
                            default=None, dest="workflow_id")
    sub_parser.add_argument("--all", action="store_true", help="Display all workflows status",
                            default=False, dest="all")
    sub_parser.add_argument("--errors", action="store_true", help="Display failed commands",
                            default=False, dest="display_errors")
    sub_parser.set_defaults(cmd_object="status")
    
    # Add available pipelines
    wf_instances, wf_methodes = wfmanager.get_available_workflows()
    wf_classes = []
    for instance in wf_instances:
        wf_classes.append(instance.__class__.__name__)
        # create the subparser for each applications
        sub_parser = subparsers.add_parser(instance.name, help=instance.description, fromfile_prefix_chars='@')
        sub_parser.convert_arg_line_to_args = instance.__class__.config_parser
        [parameters_groups, parameters_order] = instance.get_parameters_per_groups()
        for group in parameters_order:
            if group == "default":
                for param in parameters_groups[group]:
                    sub_parser.add_argument(param.flag, **param.export_to_argparse())
            elif group.startswith("exclude-"):
                is_required = False
                for param in parameters_groups[group]:
                    if param.required:
                        is_required = True
                        # an exlcusive parameter cannot be required, the require is at the group level
                        param.required = False
                pgroup = sub_parser.add_mutually_exclusive_group(required=is_required)
                for param in parameters_groups[group]:
                    pgroup.add_argument(param.flag, **param.export_to_argparse())
            else:
                pgroup = sub_parser.add_argument_group(group)
                for param in parameters_groups[group]:
                    pgroup.add_argument(param.flag, **param.export_to_argparse())
        sub_parser.set_defaults(cmd_object=instance.__class__.__name__)
    args = vars(parser.parse_args())
    
    if not "cmd_object" in args:
        print(parser.format_help())
        parser.exit(0, "")
    
    if args["cmd_object"] in wf_classes:
        wfmanager.run_workflow(args["cmd_object"], args)
    elif args["cmd_object"] == "rerun":
        wfmanager.rerun_workflow(args["workflow_id"])
    elif args["cmd_object"] == "reset":
        try:
            wfmanager.reset_workflow_component(args["workflow_id"], args["component_name"])
        except Exception as e:
            utils.display_error_message(str(e))
    elif args["cmd_object"] == "delete":
        try:
            wfmanager.delete_workflow(args["workflow_id"])
        except Exception as e:
            utils.display_error_message(str(e))
    elif args["cmd_object"] == "execution_graph":
        try:
            workflow = wfmanager.get_workflow(args["workflow_id"])
        except Exception as e:
            utils.display_error_message(str(e))
        gr = workflow.get_execution_graph()
        inputs, components = [], []
        for node in gr.nodes():
            if Workflow.INPUTFILE_GRAPH_LABEL in gr.node_attributes(node):
                inputs.append(gr.node_attributes(node)[1])
            elif Workflow.INPUTFILES_GRAPH_LABEL in gr.node_attributes(node):
                inputs.append(gr.node_attributes(node)[1])
            elif Workflow.INPUTDIRECTORY_GRAPH_LABEL in gr.node_attributes(node):
                inputs.append(gr.node_attributes(node)[1])
            elif Workflow.COMPONENT_GRAPH_LABEL in gr.node_attributes(node):
                components.append(gr.node_attributes(node)[1])
        print(("inputs: ", inputs))
        print(("components: ", components))
        print(("edges: ", gr.edges()))
        
    elif args["cmd_object"] == "status":
        if args["workflow_id"]:
            try:
                workflow = wfmanager.get_workflow(args["workflow_id"])
            except Exception as e:
                utils.display_error_message(str(e))
            print((Workflow.get_status_under_text_format(workflow, True, args["display_errors"])))
        else:
            try:
                workflows = wfmanager.get_workflows(use_cache=True)
            except Exception as e:
                utils.display_error_message(str(e))
            if len(workflows) > 0:
                workflows_by_id, wfids = {}, []
                # first sort workflow by ID
                for workflow in workflows:
                    wfids.append(workflow.id)
                    workflows_by_id[workflow.id] = workflow
                status = "ID\tNAME\tSTATUS\tELAPSED_TIME\tSTART_TIME\tEND_TIME\n"
                for i, wfid in enumerate(sorted(wfids, reverse=True)):
                    status += Workflow.get_status_under_text_format(workflows_by_id[wfid])
                    if i<len(workflows)-1: status += "\n"
            else: status = "no workflow available"
            print(status)
            