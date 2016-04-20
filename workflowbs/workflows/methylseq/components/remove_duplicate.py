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

class RemoveDuplicate (Component):

    def define_parameters(self, bams, is_paired=True, cpu=1, mem="1G"):
        self.add_input_file_list( "bam", "SORTED by coordinate bam files.", default=bams, required=True )
        names=[]
        self.temp_sorted1=[]
        self.temp_sorted2=[]
        self.temp_rmdup=[]
        for file in bams :
            f=os.path.splitext(os.path.basename(file))[0]
            names.append(os.path.splitext(os.path.basename(file))[0])
            self.temp_rmdup.append(os.path.join(self.output_directory,f+"_rmdup.bam"))
            
        self.add_parameter("is_paired", "Does library is paired ? ", default=is_paired, type="bool")
        self.add_parameter("mem", "Memory for samtools ", default=mem, type="string")
        self.add_parameter("cpu", "Cpu for samtools ", default=cpu, type="int")
        self.add_output_file_list("flagstat_init", "Flagstat initially", pattern='{basename_woext}.init_flagstat', items=self.bam)
        self.add_output_file_list("flagstat_rmdup", "Flagstat result after rmdup", pattern='{basename_woext}.rmdup_flagstat', items=self.bam)
        self.add_output_file_list("flagstat_finally", "Flagstat result after removing singleton", pattern='{basename_woext}.finally_flagstat', items=self.bam)

        self.add_output_file_list("output_bam", "The bam with removed duplicates (and singleton if paired)", pattern='{basename_woext}_clean.bam', items=self.bam)
        
        self.add_output_file_list("rmdup_stderr", "The error trace file", pattern='{basename_woext}_rmdup.stderr', items=self.bam)
        self.add_output_file_list("rmsinglet_stderr","The error trace file", pattern='{basename_woext}_rmsinglet.stderr', items=self.bam)
         
    def process(self):
        self.add_shell_execution(self.get_exec_path("samtools") + " flagstat $1 > $2", cmd_format='{EXE} {IN} {OUT}',
                                inputs=[self.bam], outputs=[self.flagstat_init], map=True)
        if self.is_paired :
            #samtools rmdup
            self.add_shell_execution(self.get_exec_path("samtools") + " rmdup $1 $2 2>> $3", cmd_format='{EXE} {IN} {OUT}',
                                inputs=[self.bam], outputs=[self.temp_rmdup,self.rmdup_stderr], map=True)
            self.add_shell_execution(self.get_exec_path("samtools") + " flagstat $1 > $2", cmd_format='{EXE} {IN} {OUT}',
                    inputs=[self.temp_rmdup], outputs=[self.flagstat_rmdup], map=True)
            #remove singleton after rmdup
            
            self.add_shell_execution(self.get_exec_path("samtools") + " sort -n -m "+self.mem+" -@"+str(self.cpu)+" $1 | "+ \
                                 self.get_exec_path("samtools") + " view -h -@"+str(self.cpu)+" -h - | "+\
                                 "awk '/^@/{print;next}$1==id{print l\"\\n\"$0;next}{id=$1;l=$0}' | "  + \
                                 self.get_exec_path("samtools") + " sort -m "+self.mem+" -@"+str(self.cpu)+" - > $2 2>>$3", 
                                 cmd_format='{EXE} {IN} {OUT}',
                                 inputs=[self.temp_rmdup], outputs=[self.output_bam,self.rmsinglet_stderr], map=True)
        else :
            #samtools rmdup
            self.add_shell_execution(self.get_exec_path("samtools") + " rmdup -s $1 $2 2>> $3", cmd_format='{EXE} {IN} {OUT}',
                                inputs=[self.bam], outputs=[self.output_bam,self.rmdup_stderr], map=True)
           
        self.add_shell_execution(self.get_exec_path("samtools") + " flagstat $1 > $2", cmd_format='{EXE} {IN} {OUT}',
                    inputs=[self.output_bam], outputs=[self.flagstat_finally], map=True)
        
