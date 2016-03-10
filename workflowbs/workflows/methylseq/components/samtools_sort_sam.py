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

class SamtoolsSortSam (Component):

    def define_parameters(self, bam_files, cpu=1, mem="1G"):
        self.add_input_file_list( "bam_files", "path to bam. These files will be used to build the id list of kept reads. ", default=bam_files, required=True )
        self.add_parameter("mem", "Memory for samtools ", default=mem, type="string")
        self.add_parameter("cpu", "Cpu for samtools ", default=cpu, type="int")
        
        self.add_output_file_list("bamsort_files", "The bam sort file", pattern='{basename_woext}_sort.bam', items=self.bam_files)
        self.add_output_file_list("sort_stderr", "The samtools sort stderr file",  pattern='{basename_woext}_sort.stderr', items=self.bam_files)
        self.add_output_file_list("sam_files", "The SAM outputed file", pattern='{basename_woext}.sam', items=self.bam_files)
        
    def process(self):
        
        self.add_shell_execution(self.get_exec_path("samtools") + " sort -m "+self.mem+" -@"+str(self.cpu)+" $1 -o $2 2>> $4;" \
                                 + self.get_exec_path("samtools") + " view -@"+str(self.cpu)+" -h $2 -o $3 2>> $4", 
                                 inputs=self.bam_files, outputs=[self.bamsort_files,self.sam_files, self.sort_stderr], map=True, cmd_format="{EXE} {IN} {OUT}")
