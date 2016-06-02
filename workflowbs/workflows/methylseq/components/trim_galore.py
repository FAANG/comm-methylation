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

from jflow.component import Component

class TrimGalore (Component):
    
    def define_parameters(self, input_files_R1, input_files_R2=None, non_directional=False, rrbs=False, quality=20, phred64=False, adapter=None, stringency=1, error_rate=0.1, length=20):
        ends_with=""
        if input_files_R1[0].endswith('.gz') :
            ends_with='.gz'
        self.add_input_file_list( "input_files_R1", "input files read1", default=input_files_R1, required=True, file_format = 'fastq')
        self.add_output_file_list( "report_files_R1", "report files read1", pattern='{basename}_trimming_report.txt', items=self.input_files_R1)
        if input_files_R2 :
            self.add_output_file_list( "output_files_R1", "output files read1", pattern='{basename_woext}_val_1.fq'+ends_with, items=self.input_files_R1)
            self.is_paired = True
            self.add_input_file_list( "input_files_R2", "input files read2", default=input_files_R2, required=True, file_format = 'fastq')
            self.add_output_file_list( "output_files_R2", "output files read2", pattern='{basename_woext}_val_2.fq'+ends_with, items=self.input_files_R2)
            self.add_output_file_list( "report_files_R2", "report files read2", pattern='{basename}_trimming_report.txt', items=self.input_files_R2)
        else :
            self.add_output_file_list( "output_files_R1", "output files read1", pattern='{basename_woext}_trimmed.fq'+ends_with, items=self.input_files_R1)
            self.output_files_R2=None
            self.is_paired = False
        self.add_output_file_list( "stderrs", "stderr files", pattern='{basename_woext}.stderr', items=self.input_files_R1)
        self.add_output_file_list( "stdouts", "stdout files", pattern='{basename_woext}.stdout', items=self.input_files_R1)        
        self.add_parameter("quality", "Quality threshold to trim low-quality ends from reads in addition to adapter removal ", default=quality,type='int')
        self.add_parameter("phred64", "Instructs Cutadapt to use ASCII+64 instead of ASCII+33", default=phred64, type="bool")
        self.add_parameter("adapter", "Adapter sequence to be trimmed", default=adapter)
        self.add_parameter("stringency", "Overlap with adapter sequence required to trim a sequence.", default=stringency, type="int")
        self.add_parameter("error_rate", "Maximum allowed error rate ", default=error_rate, type="float")
        self.add_parameter("length", "Discard reads that became shorter than length", default=length, type="int")
                        
        self.add_parameter("rrbs", "is rrbs data", default=rrbs, type="bool")
        self.add_parameter("non_directional", "Selecting this option for non-directional RRBS", default=non_directional, type="bool")
        self.options =  " --quality "+str(self.quality)+" --stringency "+ str(self.stringency) +" -e " + str(self.error_rate) +" --length " + str(self.length)
        if self.adapter != None and self.adapter != "" :
            self.options += " --adapter "+self.adapter
            
        if self.is_paired :
            self.options += " --paired"
        
        if self.rrbs :
            self.options += " --rrbs"
            if self.non_directional :
                self.options += " --non_directional"
            if self.is_paired :
                 self.options += " --trim1"
        
        if self.phred64 : 
            self.options += " --phred64"    
        
        #cutadapt path
        cutadapt_path = self.get_exec_path("cutadapt")
        self.options += " --path_to_cutadapt "+cutadapt_path
        
    def process(self):
        
        if self.is_paired: 
            self.add_shell_execution(self.get_exec_path("trim_galore") + " " + self.options + \
                            " -o " + self.output_directory + " $1 $2 >$3 2>> $4 ", cmd_format='{EXE} {IN} {OUT}',
                            inputs=[self.input_files_R1, self.input_files_R2], 
                            outputs=[self.stderrs,self.stdouts,self.output_files_R1,self.output_files_R2,self.report_files_R1,self.report_files_R2],
                            map=True)
        else : 
            self.add_shell_execution(self.get_exec_path("trim_galore") + " " + self.options + \
                            " -o " + self.output_directory + " $1 > $2 2>> $3 ", cmd_format='{EXE} {IN} {OUT}',
                            inputs=[self.input_files_R1], outputs=[self.stderrs,self.stdouts,self.output_files_R1,self.report_files_R1],
                            map=True)
 
