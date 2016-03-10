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
from jflow.component import Component

class MethylKitExtractor (Component):

    def define_parameters(self, sam_files, cov, id_reference, context, cpu=1, mem="1G"):
        self.add_input_file_list( "sam_files", "path to sorted sam. ", default=sam_files, required=True )
        self.add_parameter("coverage", "Minimum read coverage", default=cov, required=True)
        self.add_parameter("id_reference", "Which id reference genome should be used", default=id_reference, required=True)
        self.add_parameter("context", "Type of methylation context : One of the 'CpG','CHG','CHH' or 'none' strings. By default = CpG", default=context, required=True)
        self.add_output_file_list("methylkit_files", "The MethylKit output files", pattern='{basename_woext}_' + self.context + '.txt', items=self.sam_files)
        
        self.add_output_file("stdout", "The MethylKitExtractor stdout file", filename="methylkit_extractor.stdout")
        self.add_output_file_list("stderr", "The MethylKitExtractor stderr file",  pattern='{basename_woext}.stderr', items=self.methylkit_files)
        
    def process(self):
        
        self.add_shell_execution(self.get_exec_path("Rscript") + " " + self.get_exec_path("MethylKitReadBismark.R") + " -f $1 -R " + self.id_reference + " -c " + self.context + 
                                 " -m " + self.coverage + " -o $2 2>> $3", 
                                 inputs=self.sam_files, outputs=[self.methylkit_files,self.stderr], map=True, cmd_format="{EXE} {IN} {OUT}")
        
        
