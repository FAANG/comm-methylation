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

class MethylKitDM (Component):

    def define_parameters(self, meth_files, pool1, pool2, id_reference, context, normalization=False, filter=False,correct='BH',alpha=0.05):
        
        self.add_input_file_list( "meth_files", "The differential methylation output file", default=meth_files, required=True )
        self.add_parameter_list("pool1","Pool1", default=pool1, required=True)
        self.add_parameter_list("pool2","Pool2", default=pool2, required=True)
        self.add_parameter("id_reference", "Which id reference genome should be used", default=id_reference, required=True)
        self.add_parameter("context", "Type of methylation context : One of the 'CpG','CHG','CHH' or 'none' strings. By default = CpG", default=context, required=True)
        self.add_parameter("normalization", "perform methylKit logical normalization", default=normalization)
        self.add_parameter("filter", "filter position with coverage less than 5 and with coverage above 99% quantile", default=filter)
        self.add_parameter("correct", "method to adjust p-values for multiple testing ", default=correct)
        self.add_parameter("alpha", "significance level of the tests (i.e. acceptable rate of false-positive in the list of DMC)", default=alpha)
        
        self.add_output_file("diff_file", "The differential methylation outputed file", filename='DMC.txt')
        self.add_output_file("stderr", "The MethylKitDM stderr file", filename='methylkit_DM.stderr')
        
    def process(self):
        self.add_shell_execution(self.get_exec_path("Rscript") + " " + self.get_exec_path("MethDiffMethylKit.R") + " --files " + ",".join(self.meth_files) + 
                                 " --pool1 " + ",".join(self.pool1) +" --pool2 " + ",".join(self.pool2) + 
                                 " -R " + self.id_reference + " --normalization '"+str(self.normalization).upper()+"' --filter '"+str(self.filter).upper()+"' --alpha "+str(self.alpha)+
                                 " --correct '"+self.correct+"'  -c " + self.context + " -o $1 2>> $2", 
                                 includes=self.meth_files, outputs=[self.diff_file,self.stderr], cmd_format="{EXE} {OUT}")
        
        
        
