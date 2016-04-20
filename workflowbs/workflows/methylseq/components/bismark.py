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

from subprocess import Popen, PIPE
from jflow.component import Component

class Bismark (Component):

    """
    By default bismark launch 2 process of bowtie. In production book nb_proc x 2 processors.
    @param reference_genome : [str] Path to the reference genome (it must be indexed).
    @param input_files_R1 : [list] Paths to reads 1.
    @param input_files_R2 : [list] Paths to reads 2.
    @param samples_names : [list] The component produces one bam by samples_names. 
    @param non_directional : [bool] does library is directionnal 
    @param bowtie2 : [bool] set true to use bowtie2 instead of bowtie 1
    @param alignment_mismatch : [int]
    @param max_insert_size : [int] default 800
    @param description : [str] analysis description
    @param nb_proc : [int] nb proc to use for bowtie thread.
    """
    def define_parameters(self, reference_genome, input_files_R1, input_files_R2=None, samples_names=None, non_directional = False, bowtie1 = False, alignment_mismatch=1, max_insert_size=800, cpu=2, mem="1G"):
        self.add_input_file( "reference_genome", "input reference genome", default=reference_genome, required=True, file_format = 'fasta')
        self.reference_directory = os.path.dirname(reference_genome)
        self.add_input_file_list( "input_files_R1", "input files read1", default=input_files_R1, required=True, file_format='fastq')
        self.add_parameter_list( "samples_names", "The component produces one bam by prefix.", default=samples_names )
        self.add_parameter("non_directional", "Does library is non directional ? ", default=non_directional, type="bool")
        self.add_parameter("bowtie1", "Use bowtie1 ? ", default=bowtie1, type="bool")
        self.add_parameter("alignment_mismatch", "alignment_mismatch", default=alignment_mismatch, type="int")
        self.add_parameter("max_insert_size", "max_insert_size", default=max_insert_size, type="int")
        self.add_parameter("cpu", "cpu allocated for bismark (divided by 2 for bowtie option)", default=cpu, type="int")
        self.add_parameter("mem", "memory", default=mem, type="str")
        
        self.source_file = self.reference_genome + "_source"
        extention_bowtie=""        

        if not self.bowtie1 :
            extention_bowtie="_bt2"
        if input_files_R2 :
            self.is_paired = True
            self.add_input_file_list( "input_files_R2", "input files read2", default=input_files_R2, file_format='fastq')
            self.add_output_file_list( "output_files", "output alignment file", pattern='{basename}_bismark'+extention_bowtie+'_pe.bam', items=self.input_files_R1, file_format='bam')
            self.add_output_file_list( "output_files_sort", "output alignment file", pattern='{basename}_bismark'+extention_bowtie+'_pe.sort.bam', items=self.input_files_R1, file_format='bam')
            self.add_output_file_list( "output_report", "output report file", pattern='{basename}_bismark'+extention_bowtie+'_PE_report.txt', items=self.input_files_R1)
        else :
            self.is_paired = False
            self.add_output_file_list( "output_files", "output alignment file", pattern='{basename}_bismark'+extention_bowtie+'.bam', items=self.input_files_R1, file_format='bam')
            self.add_output_file_list( "output_files_sort", "output alignment file", pattern='{basename}_bismark'+extention_bowtie+'.sort.bam', items=self.input_files_R1, file_format='bam')
            self.add_output_file_list( "output_report", "output report file", pattern='{basename}_bismark'+extention_bowtie+'_SE_report.txt', items=self.input_files_R1)
        
        base_output_names=[]
        for file in input_files_R1 :
            base_output_names.append(os.path.join(os.path.dirname(file),str.replace(os.path.splitext(os.path.basename(file))[0],"_trimmed","")))
        
        unique_name=[]
        for name in self.samples_names :
            if name not in unique_name :
                unique_name.append(name)
        
        self.add_output_file_list( "output_sample_bam", "renamed output alignment file", pattern='{basename}.bam', items=unique_name, file_format='bam')
        
        self.add_output_file_list("stderrs" , "stderrs files", pattern='{basename}.stderr', items=base_output_names)
        self.add_output_file_list("sort_stderr" , "sort_stderr files", pattern='{basename}.sort_stderr', items=base_output_names)
        self.software = "bismark"
        self.args = " --gzip --bam -q"   

        if self.alignment_mismatch :
            self.args += " -N "+ str(self.alignment_mismatch)
        if self.max_insert_size and self.is_paired:
            self.args += " --maxins "+ str(self.max_insert_size) 
        if self.non_directional :
            self.args += " --non_directional"
        if not(self.bowtie1): 
            if self.cpu :
                # 2 bowtie process are launch in directional mode so divided allocated cpu for each bowtie
                self.args += " --p "+ str(int(self.cpu/2))
            self.args += " --bowtie2"
            if not os.path.dirname(self.get_exec_path("bowtie2")) == "" :
                self.args += " --path_to_bowtie " + os.path.dirname(self.get_exec_path("bowtie2")) 
                
    def process(self):
            if self.is_paired:
                self.add_shell_execution(self.get_exec_path("bismark") + " " + self.args + " -o " + self.output_directory + " --temp_dir " + self.output_directory + \
                                " " + self.reference_directory  + " -1 $1 -2 $2 2> $4 " , cmd_format='{EXE} {IN} {OUT}',
                                inputs=[self.input_files_R1, self.input_files_R2], 
                                outputs=[self.output_files,self.stderrs,self.output_report], 
                                includes=self.reference_genome, map=True) 
                
            else:
                self.add_shell_execution(self.get_exec_path("bismark") + " " + self.args + " -o " + self.output_directory + " --temp_dir " + self.output_directory + \
                                " " + self.reference_directory  + " $1 2> $3 " , cmd_format='{EXE} {IN} {OUT}',
                                inputs=self.input_files_R1, outputs=[self.output_files,self.stderrs,self.output_report], 
                                includes=self.reference_genome, map=True)
            
           
            self.add_shell_execution(self.get_exec_path("samtools") + " sort -m "+self.mem+" -@"+str(self.cpu)+" $1 -o $2 2>>$3 ", 
                                 cmd_format='{EXE} {IN} {OUT}',
                                 inputs=[self.output_files], outputs=[self.output_files_sort,self.sort_stderr], map=True)
            if self.samples_names :
                
                merge_dict={}
                for sample,file in zip(self.samples_names, self.output_files_sort):
                    if sample in merge_dict.keys() :
                        merge_dict[sample].append(file)
                    else :
                        merge_dict[sample]=[file]
                
                for i in merge_dict.keys() :
                    if len(merge_dict[i])>1 :
                        self.add_shell_execution(self.get_exec_path("samtools") + " merge "+os.path.join(self.output_directory,i+".bam")+" "+" ".join(merge_dict[i]), includes=merge_dict[i], outputs=os.path.join(self.output_directory,i+".bam"), cmd_format='{EXE} {OUT}')
                    else:
                        self.add_shell_execution("ln -s $1 "+os.path.join(self.output_directory,i+".bam"), inputs=merge_dict[i][0], outputs=os.path.join(self.output_directory,i+".bam") ,cmd_format='{EXE} {IN}')
                    
                    
