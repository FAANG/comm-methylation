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

def remove_snp(snp, input, output):
    snp_fh=open(snp)
    snp_dict={}
    for line in snp_fh :
        if not line.startswith("#") :
            snp_dict[".".join(line.split("\t")[0:2])]=""
    snp_fh.close()
    in_fh=open(input)
    out_fh=open(output,"w")
    for line in in_fh :
        if not line.split("\t")[0] in snp_dict.keys() :
            out_fh.write(line)
    in_fh.close()
    out_fh.close()
    
    
class RemoveSnpFromMethylkit (Component):

    def define_parameters(self, files, snp):
        self.add_input_file_list("methylkit_files", "The MethylKit text files",  default=files, required=True )
        self.add_input_file( "snp", "The snp to remove from analysis. ", default=snp, file_format="vcf", required=True )
        
        self.add_output_file_list("output", "The cleaned MethylKit files", pattern='{basename}', items=self.methylkit_files)
        
    def process(self):
        
        file_for_map = [self.snp for i in range(len(self.methylkit_files))]
        self.add_python_execution(remove_snp, 
                                 inputs=[file_for_map,self.methylkit_files], outputs=self.output,
                                 map=True)
        

        
        
        
