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

### This class call perl script developped for methylKit  https://raw.githubusercontent.com/al2na/methylKit/master/exec/methCall.pl

import os
from jflow.component import Component


class MethylationCalling (Component):

    def define_parameters(self, bam_files, cov, id_reference, context, is_paired=True, no_overlap=False, phred64=False):
        self.add_input_file_list( "bam_files", "path to sorted sam. ", default=bam_files, required=True )
        self.add_parameter("coverage", "Minimum read coverage", default=cov, required=True)
        self.add_parameter_list("context", "Type of methylation context : One of the 'CpG','CHG','CHH' or 'none' strings. By default = CpG",choices=['CpG','CHG','CHH'], default=context, required=True)
        self.add_parameter("is_paired", "Does library is paired ? ", default=is_paired, type="bool")
        for c in context :
            self.add_output_file_list("methylkit_files_"+c, "The MethylKit output files for context" + c, pattern='{basename_woext}_' + c + '.txt', items=self.bam_files)
        self.add_parameter("no_overlap", "the overlapping paired reads will be ignored ", default=no_overlap, type="bool")
        self.add_parameter("phred64", "the base quality is encoding with phred64", default=phred64, type="bool")

        self.add_output_file("stdout", "The MethylKitExtractor stdout file", filename="methylkit_extractor.stdout")
        self.add_output_file_list("stderr", "The MethylKitExtractor stderr file",  pattern='{basename_woext}.stderr', items=self.bam_files)
        self.options = ""
        if is_paired :
            self.options=" --type paired_sam"
        else:
            self.options=" --type single_sam"
        if phred64 : 
            self.options+=" --phred64"
        if no_overlap :
            self.options+=" --nolap"
            
    def process(self):
        context_param =""
        context_files =[]
        context_index=3
        for c in self.context :
            context_param+=" --"+c+" $"+str(context_index)
            context_files.append(self.__getattribute__("methylkit_files_"+c))
            context_index +=1
            
        self.add_shell_execution(self.get_exec_path("samtools") + " view $1 | perl " + self.get_exec_path("methCall.pl")
                                 + " --read1 - " + self.options + context_param
                                 + " --mincov " + self.coverage + " 2>> $2", 
                                 inputs=self.bam_files, outputs=[self.stderr]+context_files, map=True, cmd_format="{EXE} {IN} {OUT}")
            
          
