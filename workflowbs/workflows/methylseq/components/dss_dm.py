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

class DssDM (Component):

    def define_parameters(self, meth_files, pool1, pool2, context, normalization="libsize", 
                          high_filter=None,low_filter=None, correct='BH',alpha=0.05, gff=None, tss=None, snp=None, 
                          dmr=False, num_c=3, prop_dmc=0.5, feature=[], num_cpu=1):
        
        self.add_input_file_list( "meth_files", "The differential methylation output file", default=meth_files, required=True )
        self.add_parameter_list("pool1","Pool1", default=pool1, required=True)
        self.add_parameter_list("pool2","Pool2", default=pool2, required=True)
        self.add_parameter("context", "Type of methylation context : One of the 'CpG','CHG','CHH' or 'none' strings. By default = CpG", default=context, required=True)
        self.add_parameter("normalization", "perform methylKit logical normalization", default=normalization)
        self.add_parameter("high_cov", "Filter bases having higher coverage than this count are removed", type="int", default=high_filter)
        self.add_parameter("low_cov", "Positions with at least one sample with a count less than low_cov are removed", type="int", default=low_filter)
        self.add_parameter("correct", "method to adjust p-values for multiple testing ", default=correct)
        self.add_parameter("alpha", "significance level of the tests (i.e. acceptable rate of false-positive in the list of DMC)", default=alpha)
        self.add_parameter("dmr", "Set to 1 to compute DMR", type="bool", default=dmr)
        self.add_parameter("num_c", "cutoff of the number of CpGs (CHH or CHG) in each region to call DMR [default=3]", type="int", default=num_c)
        self.add_parameter("prop_dmc", "cutoff of the proportion of DMCs in each region to call DMR", type="float", default=prop_dmc)
        self.add_parameter_list("feature", "features to plot ',' (e.g.  exon, intron, 5_prime_utr...)", default=feature)
        self.add_input_file("annotation", "annotation file (gff ot gtf files), used in DMC categorization", default=gff)
        self.add_input_file("tss", "file with TSS positions (files format: chr    tss    strand), used to plot methylation level around TSS", default=tss)
        self.add_input_file("snp", "vcf file of SNP", default=snp)
        self.add_output_file_list("normalized_file", "The normalized matrix methylation output file", pattern='{basename_woext}.txt', items=self.meth_files)
        self.add_output_file("diff_file", "The differential methylation output file", filename='DMC.bed')
        
        self.add_output_file("pre_stderr", "The preprocessing stderr file", filename='pre_DM.stderr')
        self.add_output_file("pre_stdout", "The preprocessing  stdout file", filename='pre_DM.stdout')
        
        self.add_output_file("stderr", "The dss stderr file", filename='dss_DM.stderr')
        self.add_output_file("stdout", "The dss stdout file", filename='dss_DM.stdout')
        self.add_parameter("num_cpu", "Number of cpu to use", type="int", default=num_cpu)
        if self.get_cpu() != None :
            self.num_cpu=self.get_cpu()
        self.pre_options= " --format methylkit"
        self.pre_includes= list(self.meth_files)
        if snp != None :
            self.pre_options += " --SNP " + self.snp
            self.pre_includes.append(self.snp)
        if self.high_cov != None :
            self.pre_options += " --highCoverage " + str(self.high_cov)
        if self.low_cov  != None :
            self.pre_options += " --lowCoverage " + str(self.low_cov)
        
            
        self.dss_options= ""
        self.dss_includes = list(self.normalized_file)
        if gff != None :
            self.dss_options += " --gff " + self.annotation
            self.dss_includes.append(self.annotation)
            if len(self.feature)> 0 :
                self.dss_options += " --type " + ",".join(self.feature)
        if tss != None :
            self.dss_options += " --tss " + self.tss
            self.dss_includes.append(self.tss)
        if dmr :
            self.dss_options += " --dmr 'TRUE' --dmr.numC " +  str(self.num_c) + " --dmr.propDMC " + str(self.prop_dmc)
        if self.num_cpu > 1 :
            self.dss_options += " --parallel 'TRUE' --ncore " + str(self.num_cpu)
            self.pre_options += " --parallel 'TRUE' --ncore " + str(self.num_cpu)
                  
    def process(self):
        self.add_shell_execution(self.get_exec_path("Rscript") + " " + self.get_exec_path("MethPreprocessing.R") + " --files " + ",".join(self.meth_files) + 
                                 " --pool1 " + ",".join(self.pool1) +" --pool2 " + ",".join(self.pool2) + self.pre_options +
                                 " --method '"+str(self.normalization)+ "' -o " + self.output_directory + " > $1 2>> $2", 
                                 includes=self.pre_includes, outputs=[self.pre_stdout,self.pre_stderr]+self.normalized_file, cmd_format="{EXE} {OUT}")
        
        
        self.add_shell_execution(self.get_exec_path("Rscript") + " " + self.get_exec_path("MethDiffDSS.R") + " -d " + self.output_directory  + 
                                 " --pool1 " + ",".join(self.pool1) +" --pool2 " + ",".join(self.pool2) + " --alpha "+str(self.alpha) + " --correct "+ self.correct + 
                                 self.dss_options + " -o " + self.output_directory + " >$1 2>>$2", 
                                 includes=self.dss_includes, outputs=[self.stdout,self.stderr], cmd_format="{EXE} {OUT}")
        
        