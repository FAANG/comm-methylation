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

           
class MethylSeq (Workflow):
    
    #===========================================================================
    # FOR cluster infrastructure
    NORMAL_MEM = "2G"
    LARGE_MEM = "10G"
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
        self.add_input_file("annotation", "annotation file (gff ot gtf files), used in DMC categorization", group="Input files")
        self.add_input_file("tss", "file with TSS positions (files format: chr    tss    strand), used to plot methylation level around TSS", group="Input files")
        
        self.add_multiple_parameter_list("input_sample", "Definition of a sample", flag="--sample", required = True, group="Sample description")
        self.add_parameter("sample_name", "Names of sample, will merge alignment of same sample", type="nospacestr", add_to = "input_sample", required = True)
        self.add_input_file_list("read1", "Read 1 data file path", add_to = "input_sample")
        self.add_input_file_list("read2", "Read 2 data file path", add_to = "input_sample")
        self.add_input_file("bam", "Alignment of sample, if set skip alignment", add_to = "input_sample")
        self.add_input_file("methylkit", "MethylKit extraction file, if set skip alignment and extraction", add_to = "input_sample")
        
        self.add_parameter("is_single", "IF BAM PROVIDED : Set true if you provide alignment of single-end library",  type="bool", default=False)

        # Bisulfite parameters
        self.add_parameter("rrbs", "Workflow for RRBS data : clean data (MspI digested material) and do not perform rmdup", type="bool", default=False, group="Protocol parameters")
        self.add_parameter("non_directional", "To set if the libraries are non directional (Default : False)", type="bool", default=False, group="Protocol parameters")
        

        #cleaning options
        self.add_parameter("quality", "Quality threshold to trim low-quality ends from reads in addition to adapter removal", type="int", default=20, group="Cleaning parameters")
        self.add_parameter("phred64", "Quality scores phred64 scale used otherwise phred33 is the default  ", type=bool, default=False, flag="--phred64", group="Protocol parameters")

        # alignment parameter
        self.add_parameter("alignment_mismatch", "Sets the number of mismatches to allowed in a seed alignment during multi-seed alignment ", type="int", default=1, group="Bismark alignment parameters")
        self.add_parameter("max_insert_size", "The maximum insert size for valid paired-end alignments.", type="int", default=800, group="Bismark alignment parameters")
        self.add_parameter("bowtie1", "Use bowtie1 instead of bowtie2 (longer, better for reads < 50bp) - default False ", type=bool, default=False, flag="--bowtie1", group="Bismark alignment parameters")
        self.add_parameter("no_rmdup", "Force to not perform rmdup ", type=bool, default=False, flag="--no-rmdup", group="Bismark alignment parameters")
        self.add_parameter("deduplicate_with", "Perform deduplication with dedulicate_bismark or samtools", choices=['bismark','samtools'], default="bismark", group="Bismark alignment parameters")

        #Methylation extraction
        self.add_parameter("coverage", "Minimum read coverage",group="Methylation extraction parameters")     
        self.add_parameter_list("context", "Type of methylation context to extract and analyze", choices=['CpG','CHG','CHH'], group="Methylation extraction parameters")
        self.add_parameter("no_overlap", "The overlapping paired reads will be ignored during extraction step  ", type=bool, default=False, flag="--no-overlap", group="Methylation extraction parameters")
        #MethylKit
        self.add_multiple_parameter_list("test_methylkit", "Which test should be used for differential methylation analysis", group="DMC/DMR parameters with methylKit and eDMR")
        self.add_parameter("test_name", "Name for test", add_to = "test_methylkit")
        self.add_parameter("pool1", "List of sample-name for pool1", required=True, add_to = "test_methylkit")         
        self.add_parameter("pool2", "List of sample-name for pool2", required=True, add_to = "test_methylkit")
        self.add_parameter("stranded", "By default reads covering both strands of a CpG dinucleotide are merged, set this flag to not merge", type="bool", default=False, add_to = "test_methylkit")
        self.add_parameter("normalization", "perform methylKit logical normalization", type="bool", default=False, add_to = "test_methylkit")
        self.add_parameter("filter", "filter position with coverage less than 5 and with coverage above 99% quantile", type="bool", default=False, add_to = "test_methylkit")
        self.add_parameter("correct", "method to adjust p-values for multiple testing ",  choices=['BH','bonferroni'], add_to = "test_methylkit")
        self.add_parameter("alpha", "significance level of the tests (i.e. acceptable rate of false-positive in the list of DMC)",  type="float", default=0.05, add_to = "test_methylkit")
        self.add_parameter("dmr", "Set this option to compute DMR", type="bool", default=False, add_to = "test_methylkit")
        self.add_parameter("num_c", "cutoff of the number of CpGs (CHH or CHG) in each region to call DMR [default=3]", type="int", default=3, add_to = "test_methylkit")
        self.add_parameter("num_dmc", "cutoff of the number DMCs in each region to call DMR [default=1]", type="int", default=1, add_to = "test_methylkit")
        self.add_parameter_list("feature", "features to plot ',' (e.g.  exon, intron, 5_prime_utr...)", add_to = "test_methylkit")
        
        
        self.add_multiple_parameter_list("test_dss", "Which test should be used for differential methylation analysis", group="DMC/DMR parameters with DSS")
        self.add_parameter("test_name", "Name for test", add_to = "test_dss")
        self.add_parameter("pool1", "List of sample-name for pool1", required=True, add_to = "test_dss")         
        self.add_parameter("pool2", "List of sample-name for pool2", required=True, add_to = "test_dss")
        self.add_parameter("normalization", "Which normalization to use", default="libsize", choices=['libsize','median','UP','RLE','LR','none'], add_to = "test_dss")
        self.add_parameter("high_cov", "Filter positions having higher coverage than this count", type="int", add_to = "test_dss")
        self.add_parameter("low_cov", "Positions with at least one sample with a count less than low_cov are removed", type="int", default=0, add_to = "test_dss")        
        self.add_parameter("correct", "method to adjust p-values for multiple testing ",  choices=['BH','bonferroni'], add_to = "test_dss")
        self.add_parameter("alpha", "significance level of the tests (i.e. acceptable rate of false-positive in the list of DMC)",  type="float", default=0.05, add_to = "test_dss")
        self.add_parameter("dmr", "Set this option to compute DMR", type="bool", default=False, add_to = "test_dss")
        self.add_parameter("num_c", "cutoff of the number of CpGs (CHH or CHG) in each region to call DMR [default=3]", type="int", default=3, add_to = "test_dss")
        self.add_parameter("prop_dmc", "cutoff of the proportion of DMCs in each region to call DMR [default=0.5]", type="float", default=0.5, add_to = "test_dss")
        self.add_parameter_list("feature", "features to plot ',' (e.g.  exon, intron, 5_prime_utr...)", add_to = "test_dss")
        
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
               if (self.is_single) :
                    prefix = "single"
               else :
                    prefix = "paired"

            if sample["methylkit"] :
                self.start_with = "methylkit"
            break
        
        # init with default / if not defined will be a list of None
        bams_files=self.input_sample["bam"]
        methylkit_files=self.input_sample["methylkit"]
        
     
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
            #fastqc on raw data
            if self.is_paired :
                fastqc_raw = self.add_component("FastQC", [ self.input_sample["read1"]+reads2_fastq, False, MethylSeq.LARGE_CPU],component_prefix=prefix+"_raw")
            else : 
                fastqc_raw = self.add_component("FastQC", [ self.input_sample["read1"], False, MethylSeq.LARGE_CPU],component_prefix=prefix+"_raw")
            #cleaning raw files (quality and adapter trimming)
            trim_galore = self.add_component("TrimGalore", [ self.input_sample["read1"], reads2_fastq, self.non_directional, self.rrbs, self.quality, self.phred64],component_prefix=prefix)
            
            if self.is_paired :
                fastqc_raw = self.add_component("FastQC", [ trim_galore.output_files_R1+trim_galore.output_files_R2, False, MethylSeq.LARGE_CPU],component_prefix=prefix+"_raw")
            else : 
                fastqc_raw = self.add_component("FastQC", [ trim_galore.output_files_R1, False, MethylSeq.LARGE_CPU],component_prefix=prefix+"_raw")      
            
            bismarkReference = self.add_component("Bismark", [indexed_ref,trim_galore.output_files_R1, trim_galore.output_files_R2, reads_sample,self.non_directional,
                                                              self.bowtie1,self.alignment_mismatch, self.max_insert_size,MethylSeq.LARGE_CPU,MethylSeq.LARGE_MEM], component_prefix=prefix)
            bams_files=bismarkReference.output_sample_bam
            #if a control genome is provided
            if self.control_genome:
                indexed_control = self.control_genome
                # index the control sequence if not already indexed
                if not os.path.exists(  os.path.join(os.path.dirname(indexed_control),"Bisulfite_Genome" )):
                    bismark_genome_preparation_control = self.add_component("BismarkGenomePreparation", [ self.control_genome, self.bowtie1], component_prefix="control")
                    indexed_control = bismark_genome_preparation_control.databank    
                bismarkControl = self.add_component("Bismark", [indexed_control,trim_galore.output_files_R1, trim_galore.output_files_R2, reads_sample,self.non_directional,
                                                                self.bowtie1,self.alignment_mismatch, self.max_insert_size,MethylSeq.LARGE_CPU,MethylSeq.LARGE_MEM],component_prefix=prefix+"_control")
            
        if self.start_with in ["fastq", "bam"] :
            if not (self.rrbs) and not (self.no_rmdup):
                if self.deduplicate_with == "bismark" :
                    dedup = self.add_component("DeduplicateBismark", [bams_files,self.is_paired,MethylSeq.LARGE_CPU,MethylSeq.LARGE_MEM], component_prefix=prefix)            
                    bams_files=dedup.output_bam
                else :
                    dedup = self.add_component("RemoveDuplicate", [bams_files,self.is_paired,MethylSeq.LARGE_CPU,MethylSeq.LARGE_MEM], component_prefix=prefix)            
                    bams_files=dedup.output_bam
            
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
            # handle several context
            methylation_extractor_component = self.add_component("MethylationCalling", 
                                                                 [bams_files, self.coverage,  self.id_reference, self.context, self.is_paired, self.no_overlap, self.phred64])
        
            
            for c in self.context :           
                methylkit_output[c]=methylation_extractor_component.__getattribute__('methylkit_files_'+c)
             
        
        for to_test in self.test_methylkit :
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
                                                              to_test["normalization"],to_test["filter"],to_test["correct"],to_test["alpha"],
                                                              to_test["stranded"],self.annotation,self.tss,self.snp_reference,
                                                              to_test["dmr"],to_test["num_c"],to_test["num_dmc"],to_test["feature"],MethylSeq.LARGE_CPU], 
                                              component_prefix=prefix_str)
        
        for to_test in self.test_dss :
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
                prefix_str=to_test["test_name"]+"_"+c+"_norm"+str(to_test["normalization"])+"_filterHigh"+str(to_test["high_cov"])+"_filterLow"+str(to_test["low_cov"])+"_"+to_test["correct"]+"_"+str(to_test["alpha"]).replace(".",",")
                methdiff = self.add_component("DssDM", [files, pool1, pool2, c,
                                                              to_test["normalization"],to_test["high_cov"],to_test["low_cov"],
                                                              to_test["correct"],to_test["alpha"], self.annotation,self.tss,self.snp_reference,
                                                              to_test["dmr"],to_test["num_c"],to_test["prop_dmc"],to_test["feature"],MethylSeq.LARGE_CPU], 
                                              component_prefix=prefix_str)
   
