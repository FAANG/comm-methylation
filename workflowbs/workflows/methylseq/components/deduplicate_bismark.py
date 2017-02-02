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

from jflow.component import Component
import os

class DeduplicateBismark (Component):

    def define_parameters(self, bams, is_paired=True,cpu=2, mem="1G"):
        self.add_input_file_list( "bam", "SORTED by name bam files.", default=bams, required=True )
        self.add_parameter("is_paired", "Does library is paired ? ", default=is_paired, type="bool")
        #self.add_output_file_list("output_sort_bam", "The bam with removed duplicates (and singleton if paired)", pattern='{basename_woext}_clean.sort.bam', items=self.bam, file_format='bam')
        self.add_output_file_list("stderr", "The error trace file", pattern='{basename_woext}.dedup_stderr', items=self.bam)
        self.add_output_file_list("sort_stderr","The error trace file of sort", pattern='{basename_woext}.sort_stderr', items=self.bam)
        self.add_output_file_list("msort_stderr","The error trace file of sort", pattern='{basename_woext}.msort_stderr', items=self.bam)
        self.add_parameter("cpu", "cpu allocated for bismark (divided by 2 for bowtie option)", default=cpu, type="int")
        self.add_parameter("mem", "memory", default=mem, type="str")
        if self.get_cpu() != None :
            self.cpu=self.get_cpu()
        if self.get_memory() != None :
            self.mem=self.get_memory()
            
        self.option=""
        if not os.path.dirname(self.get_exec_path("samtools")) == "" :
            self.option= " --samtools_path " + os.path.dirname(self.get_exec_path("samtools"))
        self.option_sort=""
        if self.is_paired :
            self.option_sort= " -n "
            self.option += " -p"
            self.add_output_file_list("output_nsort", "input alignment sorted by name", pattern='{basename_woext}.bam', items=self.bam, file_format='bam')
            self.add_output_file_list("output_tmp", "input alignment sorted by name", pattern='{basename_woext}.deduplicated.bam', items=self.bam, file_format='bam')
            self.add_output_file_list("output_bam", "The bam with removed duplicates (and singleton if paired)", pattern='{basename_woext}.deduplicated.sort.bam', items=self.bam, file_format='bam')
            
        else :
            self.add_output_file_list("output_tmp", "symbolic link to input alignment", pattern='{basename_woext}.bam', items=self.bam, file_format='bam')
            self.add_output_file_list("output_bam", "The bam with removed duplicates (and singleton if paired)", pattern='{basename_woext}.deduplicated.bam', items=self.bam, file_format='bam')
            self.option += " -s"
    def process(self):
        if self.is_paired :
            self.add_shell_execution(self.get_exec_path("samtools")  + " sort "+self.option_sort+" -m "+self.mem+" -@"+str(self.cpu)+ " -o $2 $1 2> $3", cmd_format='{EXE} {IN} {OUT}',
                                inputs=[self.bam], outputs=[self.output_nsort, self.msort_stderr], map=True)
        
            self.add_shell_execution(self.get_exec_path("deduplicate_bismark") + self.option + " --bam $1 2> $2", cmd_format='{EXE} {IN} {OUT}',
                                inputs=[self.output_nsort], outputs=[self.stderr,self.output_tmp], map=True)
        
            self.add_shell_execution(self.get_exec_path("samtools")  + " sort -m "+self.mem+" -@"+str(self.cpu)+ " -o $2 $1 2> $3", cmd_format='{EXE} {IN} {OUT}',
                                inputs=[self.output_tmp], outputs=[self.output_bam, self.sort_stderr], map=True)
        else :
            self.add_shell_execution("ln -s $1 $2; " + self.get_exec_path("deduplicate_bismark") + self.option + " --bam $2 2> $3", cmd_format='{EXE} {IN} {OUT}',
                                inputs=[self.bam], outputs=[self.output_tmp,self.stderr,self.output_bam], map=True)
        