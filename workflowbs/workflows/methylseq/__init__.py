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

from jflow.workflow import Workflow

import shutil
import glob
import os

def move_pattern_file(pattern, dest_dir):
    files = glob.iglob(pattern)
    for file in files:
        if os.path.isfile(file):
            shutil.move(file, dest_dir)
            
class MethylSeq (Workflow):
    
    #===========================================================================
    # FOR cluster infrastructure
    NORMAL_MEM = "2G"
    LARGE_MEM = "8G"
    HUGE_MEM = "20G"
     
    NORMAL_CPU = 2
    LARGE_CPU = 8
    HUGE_CPU = 12
    #===========================================================================
    
    #===========================================================================
    # FOR local computer
    # NORMAL_MEM = "1G"
    # LARGE_MEM = "1G"
    # HUGE_MEM = "1G"
    
    # NORMAL_CPU = 1
    # LARGE_CPU = 2
    # HUGE_CPU = 4
    #===========================================================================

    
    def get_description(self):
        return "Align BSseq reads against a reference genome"

    def define_parameters(self, function="process"):
        self.add_input_file("reference_genome", "Which genome should the read being align on", file_format="fasta", required=True, group="Input files")
        self.add_input_file("control_genome", "Control reference sequence", file_format="fasta", group="Input files")
        self.add_input_file("snp_reference", "VCF file of known SNP to remove from the analysis",  group="Input files")
        
        self.add_multiple_parameter_list("input_sample", "Definition of a sample", flag="--sample", required = True, group="Sample description")
        self.add_parameter("sample_name", "Names of sample, will merge alignment of same sample", type="nospacestr", add_to = "input_sample", required = True)
        self.add_input_file_list("read1", "Read 1 data file path", add_to = "input_sample")
        self.add_input_file_list("read2", "Read 2 data file path", add_to = "input_sample")
        self.add_input_file("bam", "Alignment of sample, if set skip alignment", add_to = "input_sample")
        self.add_input_file("methylkit", "MethylKit extraction file, if set skip alignment and extraction", add_to = "input_sample")
        
        self.add_parameter("is_single", "IF BAM PROVIDED : Set true if you provide alignment of single-end library",  type="bool", default=False)
        # Bisulfite parameters 
        self.add_parameter("rrbs", "Workflow for RRBS data : clean data (digested with MspI) and do not perform rmdup", type="bool", default=False, group="Protocol parameters")
        self.add_parameter("non_directional", "To set if the libraries are non directional (Default : False)", type="bool", default=False, group="Protocol parameters")
        
        # alignment parameter
        self.add_parameter("alignment_mismatch", "Sets the number of mismatches to allowed in a seed alignment during multi-seed alignment ", type="int", default=1, group="Bismark alignment parameters")
        self.add_parameter("max_insert_size", "The maximum insert size for valid paired-end alignments.", type="int", default=800, group="Bismark alignment parameters")
        self.add_parameter("bowtie1", "Use bowtie1 instead of bowtie2 (longer, better for reads < 50bp) - default False ", type=bool, default=False, flag="--bowtie1", group="Bismark alignment parameters")
        self.add_parameter("no_rmdup", "Force to not perform rmdup ", type=bool, default=False, flag="--no-rmdup", group="Bismark alignment parameters")

        #Methylation extraction
        self.add_parameter("coverage", "Minimum read coverage",group="Methylation extraction parameters (methylkit)")     
        self.add_parameter_list("context", "Type of methylation context to extract and analyze", choices=['CpG','CHG','CHH'], group="Methylation extraction parameters (methylkit)")
        
        #MethylKit
        self.add_multiple_parameter_list("test", "Which test should be used for differential methylation analysis", group="DMC parameters")
        self.add_parameter("test_name", "Name for test", add_to = "test")
        self.add_parameter("pool1", "List of sample-name for pool1", required=True, add_to = "test")         
        self.add_parameter("pool2", "List of sample-name for pool2", required=True, add_to = "test")
        self.add_parameter("normalization", "perform methylKit logical normalization", type="bool", default=False, add_to = "test")
        self.add_parameter("filter", "filter position with coverage less than 5 and with coverage above 99% quantile", type="bool", default=False, add_to = "test")
        self.add_parameter("correct", "method to adjust p-values for multiple testing ",  choices=['BH','bonferroni'], add_to = "test")
        self.add_parameter("alpha", "significance level of the tests (i.e. acceptable rate of false-positive in the list of DMC)",  type="float", default=0.05, add_to = "test")
        #output
        #self.add_parameter("output_directory", "Output directory to move files after process", required=True, group = "output")
        #self.add_parameter("clean", "clean all intermediate files", type="bool", default=False, group = "output")
        self.is_paired = False
        
    def process(self):
        
        #TODO : check_dependencies
        self.start_with="fastq"
        for sample in self.input_sample:
            if len(sample["read2"])>0 and os.path.exists(sample["read2"][0]):
                self.is_paired =True
            if sample["bam"]  :
               self.start_with = "bam"
               self.is_paired = not(self.is_single) # parameter only use if bam are provided
            if sample["methylkit"] :
                self.start_with = "methylkit"
            break
        
        # init with default / if not defined will be a list of None
        bams_files=self.input_sample["bam"]
        methylkit_files=self.input_sample["methylkit"]
        
        '''        
        if os.path.exists(self.output_directory)  :
            print ("Output directory already exists, please specify another directory\n")
            exit(1)
        '''    
        
        print ("Process will start from files : "+self.start_with+"\n")    
        self.id_reference = os.path.splitext(os.path.basename(self.reference_genome))[0]

        if self.start_with=="fastq" : 
            #get a list of sample name in same order as reads1, several fastq can be set for one sample
            reads_sample = []
            for sample in self.input_sample:
                for f1 in sample["read1"] :
                    reads_sample.append(sample["sample_name"])
            
            #Alignment against the reference genome
            indexed_ref = self.reference_genome
            # index the reference genome if not already indexed
            if not os.path.exists(  os.path.join(os.path.dirname(indexed_ref),"Bisulfite_Genome" )):
                bismark_genome_preparation = self.add_component("BismarkGenomePreparation", [self.reference_genome, self.bowtie1])
                indexed_ref = bismark_genome_preparation.databank

            #need to give None value as parameters reads2 if single library            
            reads2_fastq=None
            prefix="single"
            if self.is_paired : # paired
                reads2_fastq=self.input_sample["read2"]
                prefix="paired"
                if len(reads2_fastq) != len(self.input_sample["read1"]):
                    print ("read1: ", self.input_sample["read1"])
                    print ("read2: ", reads2_fastq)
                    print ("Samples must be all paired or all single, please run 2 pipelines for each kind of data than process to statistics analyze from methylKit files with this pipeline\n")
                    exit(1)
            #cleaning raw files (quality and adapter trimming)
            trim_galore = self.add_component("TrimGalore", [ self.input_sample["read1"], reads2_fastq, self.non_directional, self.rrbs],component_prefix=prefix)
            bismarkReference = self.add_component("Bismark", [indexed_ref,trim_galore.output_files_R1, trim_galore.output_files_R2, reads_sample,self.non_directional,
                                                              self.bowtie1,self.alignment_mismatch, self.max_insert_size,MethylSeq.HUGE_CPU,MethylSeq.NORMAL_MEM], component_prefix=prefix)
            bams_files=bismarkReference.output_sample_bam
            #if a control genome is provided
            if self.control_genome:
                indexed_control = self.control_genome
                # index the control sequence if not already indexed
                if not os.path.exists(  os.path.join(os.path.dirname(indexed_control),"Bisulfite_Genome" )):
                    bismark_genome_preparation_control = self.add_component("BismarkGenomePreparation", [ self.control_genome, self.bowtie1], component_prefix="control")
                    indexed_control = bismark_genome_preparation_control.databank    
                bismarkControl = self.add_component("Bismark", [indexed_control,trim_galore.output_files_R1, trim_galore.output_files_R2, reads_sample,self.non_directional,
                                                                self.bowtie1,self.alignment_mismatch, self.max_insert_size,MethylSeq.HUGE_CPU,MethylSeq.NORMAL_MEM],component_prefix=prefix+"_control")
            
        if self.start_with in ["fastq", "bam"] :
            if not (self.rrbs) and not (self.no_rmdup):
                rmdup = self.add_component("RemoveDuplicate", [bams_files,self.is_paired, MethylSeq.HUGE_CPU, MethylSeq.LARGE_MEM], component_prefix=prefix)            
                bams_files=rmdup.output_bam

        methylkit_output={}
        if self.start_with == "methylkit" :
            #if methylkit file provided
            if len(self.context) >1 :
            # Do not allow several context
                print ("Can not provide a methylkit files and several context only available from bam or fastq\n")
                exit(1)     
            for c in self.context :
                methylkit_output[c]=self.input_sample["methylkit"]
        else:
            #convert bam to sorted sam
            sorted_sam_component = self.add_component("SamtoolsSortSam", [bams_files, MethylSeq.HUGE_CPU, MethylSeq.LARGE_MEM])
                    
            # handle several context
            for c in self.context :
                if c != None or c!="None":
                    #Launch extraction per context
                    methylation_extractor_component = self.add_component("MethylKitExtractor", 
                                                                         [sorted_sam_component.sam_files, self.coverage, self.id_reference, c], 
                                                                         component_prefix=c)
                    methylkit_output[c]=methylation_extractor_component.methylkit_files
        
        if self.snp_reference != None :
            # handle several context
            for c in methylkit_output.keys() :
                removesnp_component = self.add_component("RemoveSnpFromMethylkit", [methylkit_output[c], self.snp_reference],component_prefix=c)
                # replace files for next step
                methylkit_output[c]=removesnp_component.output
        for to_test in self.test :
            #prepare test inputs
            for c in methylkit_output.keys() :
                # associate list of files and pools for each test
                files=[]
                pool1=[]
                pool2=[]
                for sample_name,meth_file in zip(self.input_sample["sample_name"], methylkit_output[c]):
                    if sample_name in to_test["pool1"]:
                        files.append(meth_file)
                        pool1.append(os.path.basename(meth_file))
                    if sample_name in to_test["pool2"]:
                        files.append(meth_file)
                        pool2.append(os.path.basename(meth_file))
                prefix_str=to_test["test_name"]+"_"+c+"_norm"+str(to_test["normalization"])+"_filter"+str(to_test["filter"])+"_"+to_test["correct"]+"_"+str(to_test["alpha"]).replace(".",",")
                methdiff = self.add_component("MethylKitDM", [files, pool1, pool2, self.id_reference, c,
                                                              to_test["normalization"],to_test["filter"],to_test["correct"],to_test["alpha"]], 
                                              component_prefix=prefix_str)
    '''    
    def post_process(self):
        
        os.mkdir(self.output_directory)
        out_log=os.path.join(self.output_directory,"log")
        os.mkdir(out_log)
        component_to_save = ["TrimGalore","Bismark", "MethylKitExtractor","MethylKitDM", "RemoveDuplicate","RemoveSnpFromMethylkit"]
        for c_name in self.get_components_nameid() :
            
            (cpt_name,prefix)=c_name.split(".")
            cpt_dir = self.get_component_output_directory(cpt_name,prefix)
            shutil.move(os.path.join(cpt_dir,"trace.txt"),os.path.join(out_log,c_name+".log"))
            if cpt_name in component_to_save :
            
                curr_out_dir=os.path.join(self.output_directory,cpt_name+"_"+prefix)
                os.mkdir(curr_out_dir)
                if c_name.startswith("TrimGalore"):
                    #copy reports
                    move_pattern_file(os.path.join(cpt_dir,"*_report.txt"),curr_out_dir)
                
                if c_name.startswith("Bismark"):
                    #copy bam and report
                    #move_pattern_file(os.path.join(cpt_dir,"*.bam"),curr_out_dir)
                    move_pattern_file(os.path.join(cpt_dir,"*_report.txt"),curr_out_dir)
                
                if c_name.startswith("MethylKitExtractor"):
                    #copy extract positions
                    move_pattern_file(os.path.join(cpt_dir,"*.txt"),curr_out_dir)
                
                if c_name.startswith("RemoveSnpFromMethylkit"):
                    #copy extract positions
                    move_pattern_file(os.path.join(cpt_dir,"*.txt"),curr_out_dir)
                
                if c_name.startswith("MethylKitDM"):
                    #copy extract positions
                    move_pattern_file(os.path.join(cpt_dir,"*"),curr_out_dir)
                
                if c_name.startswith("RemoveDuplicate")  :
                    #copy final bam
                    move_pattern_file(os.path.join(cpt_dir,"*_clean.bam"),curr_out_dir)
                    #copy flagstat
                    move_pattern_file(os.path.join(cpt_dir,"*_flagstat"),curr_out_dir)

            if self.clean :
                shutil.rmtree(cpt_dir)
    '''    
