#
# Copyright (C) 2012 INRA
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

from jflow.component import Component

class FastQC (Component):
    
    def define_parameters(self, input_files, no_group=False, num_cpu = 3):
        """
          @param input_files : paths
          @param is_casava : True gathers all different files of one read of one sample (only with name on CASAVA 1.8+ format)
          @param no_group : True disables grouping of bases for reads >50bp
          @param archive_name : name for the output archive
        """
        self.add_input_file_list( "input_files", "Fastq files paths", default=input_files, required=True, file_format = 'fastq')
        self.add_parameter("no_group", "True disables grouping of bases for reads >50bp", default=no_group, type='bool')
        self.add_parameter("num_cpu", "Number of threads for fastqc", default=num_cpu)
        if self.get_cpu() != None :
            self.num_cpu=self.get_cpu()
        items = self.input_files
        
        self.add_output_file_list( "stdouts", "Fastqc stdout files", pattern='{basename_woext}.stdout', items=items)
        self.add_output_file_list( "stderrs", "Fastqc stderr files", pattern='{basename_woext}.stderr', items=items)
            
        self.options = " -f fastq " 
        if self.no_group:
            self.options += " --nogroup"

    def process(self):
         self.add_shell_execution(self.get_exec_path("fastqc") + ' -t ' + str(self.num_cpu) + 
                                  ' --extract --outdir ' + self.output_directory + ' ' + self.options + ' $1 '  + ' > $2 2> $3', 
                                  cmd_format='{EXE} {IN} {OUT}',
                                  inputs=self.input_files, 
                                  outputs=[self.stdouts,self.stderrs],
                                  map=True)
