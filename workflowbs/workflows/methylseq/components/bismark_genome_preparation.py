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


from jflow.component import Component
from jflow.utils import which

from weaver.function import PythonFunction


def bismark_index(input_fasta, databank_directory, databank_fasta, stdout_path, stderr_path, exec_path, args=""):
    from subprocess import Popen, PIPE
    import shlex
    # first make the symbolic link
    os.symlink(input_fasta, databank_fasta)
    # execute bwt2 index
    command_line = args.strip('\'')
    command_line = exec_path + " " + command_line + " " + databank_directory
    cmd = shlex.split(command_line)
    
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    # write down the stdout
    stdoh = open(stdout_path, "w")
    stdoh.write(str(stdout))
    stdoh.close()
    # write down the stderr
    
    stdeh = open(stderr_path, "w")
    stdeh.write(str(stderr))
    stdeh.close()
        
class BismarkGenomePreparation (Component):
    
    def define_parameters(self, reference_genome, bowtie1=False):

        self.add_input_file( "reference_genome", "input reference genome", default=reference_genome, required=True, file_format = 'fasta')

        #define link to fasta
        self.add_output_file("databank", "The indexed databank to use with bowtie", filename=os.path.basename(self.reference_genome), file_format="fasta")
        self.add_output_file("stdout", "The bismark_genome_preparation stdout file", filename="bismark_genome_preparation.stdout")
        self.add_output_file("stderr", "The bismark_genome_preparation stderr file", filename="bismark_genome_preparation.stderr")
        self.add_parameter("bowtie1", "bowtie1", default=bowtie1, type='bool')
        
        self.args = ""
        
        if not self.bowtie1: 
            btw_param = " --bowtie2"
            if not os.path.dirname(self.get_exec_path("bowtie2")) == "" :
                btw_param += " --path_to_bowtie " + os.path.dirname(self.get_exec_path("bowtie2")) 
            self.args += "\\'"+btw_param+"\\'"
            
    def process(self):
        self.add_python_execution(bismark_index, cmd_format="{EXE} {IN} {OUT} {ARG}",
                                  inputs=[self.reference_genome,self.output_directory], 
                                  outputs=[self.databank, self.stdout, self.stderr], 
                                  arguments=[self.get_exec_path("bismark_genome_preparation"), self.args ])
