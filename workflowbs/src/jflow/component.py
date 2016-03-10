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
import tempfile
import types

from operator import attrgetter

from jflow.workflows_manager import WorkflowsManager
from jflow.config_reader import JFlowConfigReader
from jflow.dataset import ArrayList
from jflow.utils import which, display_error_message
from jflow.parameter import *
from jflow.abstraction import MultiMap

from weaver.util import parse_string_list
from weaver.function import ShellFunction
from weaver.abstraction import Map
from weaver.function import PythonFunction


class Component(object):
    
    TRACE_FILE_NAME = "trace.txt"
    
    def __init__(self):
        self.prefix = "default"
        self.params_order = []
        self.output_directory = None
        self.config_reader = JFlowConfigReader()
        self.version = self.get_version()
        if isinstance(self.version, bytes):
            self.version = self.version.decode()
        self.batch_options = self.config_reader.get_component_batch_options(self.__class__.__name__)

    def is_dynamic(self):
        return len(self.get_dynamic_outputs()) != 0

    def get_dynamic_outputs(self):
        """
         @return : the list of outputs updated at the end of component execution.
        """
        dynamic_outputs = list()
        for attribute_value in list(self.__dict__.values()):
            if issubclass( attribute_value.__class__, DynamicOutput ):
                dynamic_outputs.append( attribute_value )
        return dynamic_outputs

    def get_output_files(self):
        outputs = {}
        for attribute_value in list(self.__dict__.values()):
            if ( issubclass( attribute_value.__class__, DynamicOutput ) or
                 issubclass( attribute_value.__class__, OutputFileList) ):
                for f in attribute_value:
                    outputs[os.path.basename(f)] = f
            elif issubclass( attribute_value.__class__, OutputFile):
                outputs[os.path.basename(attribute_value)] = attribute_value
        return outputs

    def add_input_directory(self, name, help, default=None, required=False, flag=None, 
                            group="default",  
                            display_name=None, cmd_format="", argpos=-1):
        new_param = InputDirectory(name, help, flag=flag, default=default, required=required, group=group, 
                                   display_name=display_name, cmd_format=cmd_format, argpos=argpos)
        # store where the parameter is coming from
        new_param.linkTrace_nameid = self.get_nameid()
        if issubclass( default.__class__, LinkTraceback ):
            new_param.parent_linkTrace_nameid = [default.linkTrace_nameid]
        # add it to the class itself
        self.params_order.append(name)
        self.__setattr__(name, new_param)

    def add_input_file(self, name, help, file_format="any", default=None, type="inputfile", 
                       required=False, flag=None, group="default", display_name=None, 
                       cmd_format="", argpos=-1):
        new_param = InputFile(name, help, flag=flag, file_format=file_format, default=default, 
                              type=type, required=required, group=group, display_name=display_name, 
                              cmd_format=cmd_format, argpos=argpos)
        # store where the parameter is coming from
        new_param.linkTrace_nameid = self.get_nameid()
        if issubclass( default.__class__, LinkTraceback ):
            new_param.parent_linkTrace_nameid = [default.linkTrace_nameid]
        # add it to the class itself
        self.params_order.append(name)
        self.__setattr__(name, new_param)
    
    def reset(self):
        for file in os.listdir(self.output_directory):
            os.remove(os.path.join(self.output_directory, file))
    
    def add_input_file_list(self, name, help, file_format="any", default=None, type="inputfile", 
                            required=False, flag=None, group="default", display_name=None,
                            cmd_format="", argpos=-1):
        if default == None:
            inputs = []
        elif issubclass(default.__class__, list):
            inputs = [IOFile(file, file_format, self.get_nameid(), None) for file in default]
        else:
            inputs = [IOFile(default, file_format, self.get_nameid(), None)]
        new_param = InputFileList(name, help, flag=flag, file_format=file_format, default=inputs, 
                                  type=type, required=required, group=group, display_name=display_name,
                                  cmd_format=cmd_format, argpos=argpos)
        # store where the parameter is coming from
        new_param.linkTrace_nameid = self.get_nameid()
        if issubclass( default.__class__, list ):
            for idx, val in enumerate(default):
                if issubclass( val.__class__, LinkTraceback ):
                    new_param[idx].parent_linkTrace_nameid = [val.linkTrace_nameid]
                    if not val.linkTrace_nameid in new_param.parent_linkTrace_nameid:
                        new_param.parent_linkTrace_nameid.append( val.linkTrace_nameid )
        else:
            if issubclass( default.__class__, LinkTraceback ):
                new_param[0].parent_linkTrace_nameid = [default.linkTrace_nameid]
                if not default.linkTrace_nameid in new_param.parent_linkTrace_nameid:
                    new_param.parent_linkTrace_nameid.append( default.linkTrace_nameid )
        # add it to the class itself
        self.params_order.append(name)
        self.__setattr__(name, new_param)

    def add_parameter(self, name, help, default=None, type=str, choices=None, 
                      required=False, flag=None, group="default", display_name=None,   
                      cmd_format="", argpos=-1):
        new_param = ParameterFactory.factory(name, help, flag=flag, default=default, type=type, choices=choices, 
                              required=required, group=group, display_name=display_name,  
                              cmd_format=cmd_format, argpos=argpos)
        # add it to the class itself
        self.params_order.append(name)
        self.__setattr__(name, new_param)

    def add_parameter_list(self, name, help, default=None, type=str, choices=None, 
                           required=False, flag=None, group="default", display_name=None,
                           cmd_format="", argpos=-1):
        if default == None: default = []
        new_param = ParameterList(name, help, flag=flag, default=default, type=type, choices=choices, 
                                  required=required, group=group, display_name=display_name,
                                  cmd_format=cmd_format, argpos=argpos)
        # add it to the class itself
        self.params_order.append(name)
        self.__setattr__(name, new_param)

    def add_input_object(self, name, help, default=None, required=False):
        new_param = InputObject(name, help, default=default, required=required)
        # store where the parameter is coming from
        new_param.linkTrace_nameid = self.get_nameid()
        
        if issubclass( default.__class__, list ):
            for idx, val in enumerate(default):
                if hasattr( val, "linkTrace_nameid" ):
                    if not val.linkTrace_nameid in new_param.parent_linkTrace_nameid:
                        new_param.parent_linkTrace_nameid.append(val.linkTrace_nameid)
                    new_param.default[idx].parent_linkTrace_nameid = [val.linkTrace_nameid]
                    new_param.default[idx].linkTrace_nameid = self.get_nameid()
        elif hasattr( default, "linkTrace_nameid" ):
            new_param.parent_linkTrace_nameid = [default.linkTrace_nameid]
            new_param.default.parent_linkTrace_nameid = [default.linkTrace_nameid]
            new_param.default.linkTrace_nameid = self.get_nameid()
        
        # add it to the class itself
        self.params_order.append(name)
        self.__setattr__(name, new_param)        
    
    def add_input_object_list(self, name, help, default=None, required=False):
        if default == None: default = []
        new_param = InputObjectList(name, help, default=default, required=required)
        
        # store where the parameter is coming from
        new_param.linkTrace_nameid = self.get_nameid()
        for idx, val in enumerate(new_param.default):
            if hasattr( val, "linkTrace_nameid" ):
                if not val.linkTrace_nameid in new_param.parent_linkTrace_nameid:
                    new_param.parent_linkTrace_nameid.append(val.linkTrace_nameid)
                new_param.default[idx].parent_linkTrace_nameid = [val.linkTrace_nameid]
                new_param.default[idx].linkTrace_nameid = self.get_nameid()

        # add it to the class itself
        self.params_order.append(name)
        self.__setattr__(name, new_param)
    
    def add_output_object(self, name, help, required=False):
        new_param = OutputObject(name, help, required=required)
        # store where the parameter is coming from
        new_param.linkTrace_nameid = self.get_nameid()
        new_param.default.linkTrace_nameid = self.get_nameid()
        # add it to the class itself
        self.params_order.append(name)
        self.__setattr__(name, new_param)
    
    def add_output_object_list(self, name, help, nb_items=0, required=False):
        new_param = OutputObjectList(name, help, nb_items=nb_items, required=required)
        # store where the parameter is coming from
        new_param.linkTrace_nameid = self.get_nameid()
        for idx, val in enumerate(new_param.default):
            new_param.default[idx].linkTrace_nameid = self.get_nameid()
        # add it to the class itself
        self.params_order.append(name)
        self.__setattr__(name, new_param)
        
    def add_output_file(self, name, help, file_format="any", filename=None, group="default", display_name=None,
                         cmd_format="", argpos=-1):
        filename = os.path.basename(filename)
        new_param = OutputFile(name, help, default=os.path.join(self.output_directory, filename),
                               file_format=file_format, group=group, display_name=display_name,
                               cmd_format=cmd_format, argpos=argpos)
        # store where the parameter is coming from
        new_param.linkTrace_nameid = self.get_nameid()
        # add it to the class itself
        self.params_order.append(name)
        self.__setattr__(name, new_param)

    def add_output_file_list(self, name, help, file_format="any", pattern='{basename_woext}.out', 
                             items=None, group="default", display_name=None, cmd_format="", argpos=-1):
        default = [IOFile(file, file_format, self.get_nameid(), None) for file in self.get_outputs(pattern, items)]
        new_param = OutputFileList(name, help, default=default, file_format=file_format, group=group, display_name=display_name,
                                   cmd_format=cmd_format, argpos=argpos)
        # store where the parameter is coming from
        new_param.linkTrace_nameid = self.get_nameid()
        # add it to the class itself
        self.params_order.append(name)
        self.__setattr__(name, new_param)

    def add_output_file_endswith(self, name, help, pattern, file_format="any", behaviour="include",
                               group="default", display_name=None, cmd_format="", argpos=-1):
        new_param = OutputFilesEndsWith(name, help, self.output_directory, pattern, include=(behaviour == "include"), 
                                       file_format=file_format, group=group, display_name=display_name,
                                       cmd_format=cmd_format, argpos=argpos)
        # store where the parameter is coming from
        new_param.linkTrace_nameid = self.get_nameid()
        # add it to the class itself
        self.params_order.append(name)
        self.__setattr__(name, new_param)

    def add_output_file_pattern(self, name, help, pattern, file_format="any", behaviour="include",
                               group="default", display_name=None, cmd_format="", argpos=-1):
        new_param = OutputFilesPattern(name, help, self.output_directory, pattern, include=(behaviour == "exclude"), 
                                       file_format=file_format, group=group, display_name=display_name,
                                       cmd_format=cmd_format, argpos=argpos)
        # store where the parameter is coming from
        new_param.linkTrace_nameid = self.get_nameid()
        # add it to the class itself
        self.params_order.append(name)
        self.__setattr__(name, new_param)
    
    def _longestCommonSubstr(self, data, clean_end=True):
        substr = ''
        if len(data) > 1 and len(data[0]) > 0:
            for i in range(len(data[0])):
                for j in range(len(data[0])-i+1):
                    if j > len(substr) and all(data[0][i:i+j] in x for x in data):
                        substr = data[0][i:i+j]
        else:
            substr = data[0]
        if clean_end:
            while substr.endswith("_") or substr.endswith("-") or substr.endswith("."):
                substr = substr[:-1]
        return substr

    def get_outputs(self, output_list=None, input_list=None):
        """
        If `output_list` is a string template, then it may have the following
        fields:

        - `{fullpath}`, `{FULL}`         -- Full input file path.
        - `{basename}`, `{BASE}`         -- Base input file name.
        - `{fullpath_woext}`, `{FULLWE}` -- Full input file path without extension
        - `{basename_woext}`, `{BASEWE}` -- Base input file name without extension
        """
        if output_list is None:
            return []

        if isinstance(output_list, str):
            ilist = []
            if not input_list or not '{' in str(output_list):
                if input_list is not None and len(input_list) == 0:
                    return []
                else:
                    return [output_list]
            # if multiple list of inputs is used
            elif isinstance(input_list[0], list):
                for i, val in enumerate(input_list[0]):
                    iter_values = []
                    for j, ingroup in enumerate(input_list):
                        iter_values.append(os.path.basename(input_list[j][i]))
                    ilist.append(self._longestCommonSubstr(iter_values))
            else:
                ilist = parse_string_list(input_list)
                            
            return [os.path.join(self.output_directory, str(output_list).format(
                        fullpath       = input,
                        FULL           = input,
                        i              = '{0:05X}'.format(i),
                        NUMBER         = '{0:05X}'.format(i),
                        fullpath_woext = os.path.splitext(input)[0],
                        FULL_WOEXT     = os.path.splitext(input)[0],
                        basename       = os.path.basename(input),
                        BASE           = os.path.basename(input),
                        basename_woext = os.path.splitext(os.path.basename(input))[0] if os.path.splitext(os.path.basename(input))[1] != ".gz" else os.path.splitext(os.path.splitext(os.path.basename(input))[0])[0],
                        BASE_WOEXT     = os.path.splitext(os.path.basename(input))[0] if os.path.splitext(os.path.basename(input))[1] != ".gz" else os.path.splitext(os.path.splitext(os.path.basename(input))[0])[0]))
                    for i, input in enumerate(ilist)]
    
    def execute(self):
        # first create the output directory
        if not os.path.isdir(self.output_directory):
            os.makedirs(self.output_directory, 0o751)
        # then run the component
        self.process()
    
    def process(self):
        """ 
        Run the component, can be implemented by subclasses for a 
        more complex process 
        """
        # get all parameters
        parameters = []
        inputs = []
        outputs = []
        for param_name in self.params_order:
            param = self.__getattribute__(param_name)
            if isinstance(param, AbstractParameter) :
                if isinstance(param, AbstractInputFile):
                    inputs.append(param)
                elif isinstance(param, AbstractOutputFile):
                    outputs.append(param)
                else :
                    parameters.append(param)
        
        # sort parameters using argpos
        parameters = sorted(parameters, key=attrgetter('argpos'))
        inputs = sorted(inputs, key=attrgetter('argpos'))
        outputs = sorted(outputs, key=attrgetter('argpos'))
        filteredparams = []
        commandline = self.get_exec_path(self.get_command())

        for p in parameters :
            if isinstance(p, BoolParameter) :
                if p:
                    commandline += " %s " % p.cmd_format
            else :
                if p.default :
                    commandline += " %s %s " % (p.cmd_format, p.default)
        
        abstraction = self.get_abstraction()
        
        if abstraction == None:
            cpt = 1
            for file in inputs + outputs :
                if isinstance(file, InputFile) or isinstance(file, OutputFile):
                    commandline +=  ' %s $%s ' % (file.cmd_format, cpt)
                    cpt+=1
                # input file list or output file list / pattern / ends with
                else :
                    for e in file :
                        commandline += ' %s $%s ' % (file.cmd_format, cpt)
                        cpt+=1
            function = ShellFunction( commandline,  cmd_format='{EXE} {IN} {OUT}')
            function(inputs=inputs, outputs=outputs) 
        # weaver map abstraction
        elif abstraction == 'map' :
            if not(len(inputs) == len(outputs) == 1) :
                display_error_message("You can only have one type of input and one type of output for the map abstraction")

            for file in inputs :
                commandline += ' %s $1 ' % file.cmd_format
                if isinstance(file, ParameterList) :
                    inputs = file
            
            for file in outputs :
                commandline += ' %s $2 ' % file.cmd_format
                if isinstance(file, ParameterList) :
                    outputs = file 
            
            function = ShellFunction( commandline,  cmd_format='{EXE} {IN} {OUT}')
            exe = Map(function, inputs=inputs, outputs=outputs)
        
        # jflow multimap
        elif abstraction == 'multimap' :
            cpt = 1
            for file in inputs + outputs:
                if not(isinstance(file, ParameterList)):
                    display_error_message("Multimap abstraction can be used only with ParameterList")
                commandline += ' %s $%s ' % (file.cmd_format, cpt)
                cpt+=1
            
            function  = ShellFunction( commandline,  cmd_format='{EXE} {IN} {OUT}')
            exe = MultiMap(function, inputs=inputs, outputs=outputs)
        # anything other than that will be considered errored
        else :
            raise Exception('Unsupported abstraction %s ' % abstraction)
        
    def get_command(self):
        """
            get a path to an executable. Has to be implemented by subclasses 
            if the process has not been implemented  
        """
        raise NotImplementedError("Either the Component.get_command() function or the Component.process() function has to be implemented!")
    
    def get_abstraction(self):
        """
            get the abstraction. Has to be implemented by subclasses 
            if the process has not been implemented  
        """ 
        raise NotImplementedError("Either the Component.get_abstraction() function or the Component.process() function has to be implemented!")

    def get_version(self):
        """ 
        Return the tool version, has to be implemented by subclasses
        """
        return None
    
    def get_temporary_file(self, suffix=".txt"):
        # first check if tmp directory exists
        if not os.path.isdir(self.config_reader.get_tmp_directory()):
            os.makedirs(self.config_reader.get_tmp_directory(), 0o751)
        tempfile_name = os.path.basename(tempfile.NamedTemporaryFile(suffix=suffix).name)
        return os.path.join(self.config_reader.get_tmp_directory(), tempfile_name)
    
    def define_parameters(self, *args):
        """ 
        Define the component parameters, has to be implemented by subclasses
        """
        raise NotImplementedError

    def get_resource(self, resource):
        return self.config_reader.get_resource(resource)
    
    def get_exec_path(self, software):
        exec_path = self.config_reader.get_exec(software)
        if exec_path is None and os.path.isfile(os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "../../bin", software)):
            exec_path = os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "../../bin", software)
        elif exec_path is None and os.path.isfile(os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "../bin", software)):
            exec_path = os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "../bin", software)
        elif exec_path is None and os.path.isfile(os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "bin", software)):
            exec_path = os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "bin", software)
        elif exec_path is None and which(software) == None:
            logging.getLogger("jflow").exception("'" + software + "' path connot be retrieved either in the PATH and in the application.properties file!")
            raise Exception("'" + software + "' path connot be retrieved either in the PATH and in the application.properties file!")
        elif exec_path is None and which(software) != None: 
            exec_path = software
        elif exec_path != None and not os.path.isfile(exec_path):
            logging.getLogger("jflow").exception("'" + exec_path + "' set for '" + software + "' does not exists, please provide a valid path!")
            raise Exception("'" + exec_path + "' set for '" + software + "' does not exists, please provide a valid path!")
        return exec_path
    
    def get_nameid(self):
        return self.__class__.__name__ + "." + self.prefix
    
    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.prefix == other.prefix
    
    def __getattribute__(self, attr):
        # an IOobject is a specific object defined by the presence of the dump_path attribute
        if hasattr(object.__getattribute__(self, attr), "default"):
            if isinstance (object.__getattribute__(self, attr).default, OObject) and os.path.exists(object.__getattribute__(self, attr).default.dump_path):
                object.__getattribute__(self, attr).default=object.__getattribute__(self, attr).default.load()
            if hasattr(object.__getattribute__(self, attr).default, "is_ioobject"):
                return object.__getattribute__(self, attr).default
            elif isinstance(object.__getattribute__(self, attr).default, list) and len(object.__getattribute__(self, attr).default)>0:
                if isinstance(object.__getattribute__(self, attr).default[0], OObject):
                    for i, val in enumerate (object.__getattribute__(self, attr).default):
                       if os.path.exists(val.dump_path):
                           object.__getattribute__(self, attr).default[i]=val.load()
                if hasattr(object.__getattribute__(self, attr).default[0], "is_ioobject"):
                    return object.__getattribute__(self, attr).default
            
                
        return object.__getattribute__(self, attr)
    
    def __generate_iolist (self, ioparameter, map):
        new_ios = []
        includes = []
        if map :
            if len (ioparameter) >0 :
                if isinstance(ioparameter[0], list):
                    for cin in ioparameter:
                        if hasattr(cin[0], "is_ioobject"):
                            new_ios.append([i.dump_path for i in cin])
                        else:
                            new_ios.append(cin)
                else:
                    for cin in ioparameter:
                        if hasattr(cin, "is_ioobject"):
                            new_ios.append(cin.dump_path)
                        else:
                            new_ios.append(cin)
        else :
            new_ios = []
            if hasattr(ioparameter, "is_ioobject"):
                includes.extend(ioparameter.includes)
                new_ios.append(ioparameter.dump_path)
            elif isinstance(ioparameter, list):
                for cin in ioparameter:
                    if hasattr(cin, "is_ioobject"):
                        includes.extend(cin.includes)
                        new_ios.append(cin.dump_path)
                    else:
                        new_ios.append(cin)
            else:
                new_ios = ioparameter
        return new_ios,includes
    
    def add_python_execution(self, function, inputs=[], outputs=[], arguments=[], includes=[], 
                             add_path=None, collect=False, local=False, map=False, cmd_format=""):
               
        if map:
            if arguments != [] :
                logging.getLogger("jflow").exception("add_python_execution: '" + function.__name__ + "' arguments parameter not allowed with map!")
                raise Exception("add_python_execution: '" + function.__name__ + "' arguments parameter not allowed with map!" )
            if not issubclass(inputs.__class__, list) or not issubclass(outputs.__class__, list):
                logging.getLogger("jflow").exception("add_python_execution: '" + function.__name__ + "' map requires a list as inputs and output!")
                raise Exception("add_python_execution: '" + function.__name__ + "' map requires a list as inputs and output!")
        #Command format to build
        if cmd_format == "" :
            cmd_format = "{EXE} "
            if len(arguments)>0:
                cmd_format += " {ARG}"
            if (isinstance(inputs, list) and len(inputs)>0) or (inputs is not None and inputs != []):
                cmd_format += " {IN}"
            if (isinstance(outputs, list) and len(outputs)>0) or (outputs is not None and outputs != []):
                cmd_format += " {OUT}"
        py_function = PythonFunction(function, add_path=add_path, cmd_format=cmd_format)

        
        new_inputs,includes_in = self.__generate_iolist(inputs, map)
        new_outputs,includes_out = self.__generate_iolist(outputs, map)
        if not isinstance(includes, list):
            includes=[includes]
        if map:
            MultiMap(py_function, inputs=new_inputs, outputs=new_outputs, includes=includes+includes_in, collect=collect, local=local)
        else:
            py_function(inputs=new_inputs, outputs=new_outputs, arguments=arguments, includes=includes+includes_in)
        
        self.__write_trace(function.__name__, inputs, outputs, arguments, cmd_format, map, "PythonFunction")
        
    def add_shell_execution(self, source, inputs=[], outputs=[], arguments=[], includes=[], 
                            cmd_format=None, map=False, shell=None, collect=False, local=False):
        shell_function  = ShellFunction( source, shell=shell, cmd_format=cmd_format )
       
        # if abstraction is map or multimap
        if map :
            # if input and output are list or filelist
            if issubclass(inputs.__class__, list) and issubclass(outputs.__class__, list) :
                # arguments cannot be set with 
                if arguments != [] :
                    logging.getLogger("jflow").exception("add_shell_execution: '" + source + "' arguments parameter not allowed with map")
                    raise Exception("add_shell_execution: '" + source + "' arguments parameter not allowed with map" )
                MultiMap(shell_function,inputs=inputs, outputs=outputs, includes=includes, collect=collect, local=local)
            else :
                logging.getLogger("jflow").exception("add_shell_execution: '" + source + "' map requires a list as inputs and output")
                raise Exception("add_shell_execution: '" + source + "'  map requires a list as inputs and output")
            
        else :
            shell_function( inputs=inputs, outputs=outputs, arguments=arguments, includes=includes )   
        self.__write_trace(source, inputs, outputs, arguments, cmd_format, map, "Shell")
        
    def __write_trace(self, name,  inputs, outputs, arguments, cmd_format, map, type):
        trace_fh=open(os.path.join(self.output_directory, Component.TRACE_FILE_NAME), "a")
        trace_fh.write("###\n###Execution trace of "+type+": "+name+"\n")
        if map :
            trace_fh.write("MODE MAP\n")
        
        if cmd_format != "" and type == "Shell":
            trace_fh.write("COMMAND: " + str(cmd_format) + "\n")
        self.__write_element(trace_fh,"ARGCUMENTS",arguments)
        self.__write_element(trace_fh,"INPUTS",inputs)
        self.__write_element(trace_fh,"OUTPUTS",outputs)
        trace_fh.close()
        
    def __write_element(self,fh, title, element):
        to_write=''
        if isinstance(element, list):
            if len (element)> 0 :
                if isinstance(element[0], list):
                    for i in range(len(element)) : 
                        to_write+="List"+str(i+1)+": \n"
                        to_write+="\n".join(element[i])+"\n"
                else : 
                    to_write+="\n".join(element)+"\n"
        else :
            to_write+= element+"\n"
        if to_write != "" :
            fh.write(title+" :\n")
            fh.write(to_write)
            