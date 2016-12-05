#
# Copyright (C) 2016 INRA
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
#----------------------------------------------------------------------
#authors :
#---------
#	Piumi Francois (francois.piumi@inra.fr)		software conception and development (engineer in bioinformatics)
#	Jouneau Luc (luc.jouneau@inra.fr)		software conception and development (engineer in bioinformatics)
#	Gasselin Maxime (m.gasselin@hotmail.fr)		software user and data analysis (PhD student in Epigenetics)
#	Perrier Jean-Philippe (jp.perrier@hotmail.fr)	software user and data analysis (PhD student in Epigenetics)
#	Al Adhami Hala (hala_adhami@hotmail.com)	software user and data analysis (postdoctoral researcher in Epigenetics)
#	Jammes Helene (helene.jammes@inra.fr)		software user and data analysis (research group leader in Epigenetics)
#	Kiefer Helene (helene.kiefer@inra.fr)		software user and data analysis (principal invertigator in Epigenetics)
#

"""

# Parse the output of "dig_genome_RRBS.py" (RR fragments fasta file)

# Output 
total length of the fragments (RR genome size)
number of fragments
number of CG

remove the bases added by the "dig_genome_RRBS.py" script at the end of the fragment according to the used restriction enzyme. Here only Msp1, XmaC1 or BssS1 can be used.

# Command line = ./RR_genome_parametres.py   <fragments_fasta_file.fa> <genome species> <restriction site recognition sequence ("CCGG" or "CCCGGG" or "CACGAG" or "0")>

# Output file = "stats_fragments_fasta_file.txt"

"""

from string import *
from sys import argv
import sys
import re
import os, stat



def counts(filetype,sequence, rest_site, CG_nb, fragments_number, RR_genome_size):

	# bases are added at the end of fragments in RR_genomes and must be removed in RR_genome only ! 
	# in order to correctly count the CG number
	# not in genome files
	if filetype != 'genome':
		#print filetype

	# remove added bases
		if rest_site == "CCGG":
			if re.search('CG$', sequence):
				sequence = sequence[:-2]

		elif rest_site == "CCCGGG":
			if re.search('CCGG$', sequence):
				sequence = sequence[:-4]

		elif rest_site == "CACGAG":
			if re.search('ACGA$', sequence):
				sequence = sequence[:-4]


					
	# CG number
	nom = re.compile(r'CG')
	if nom.findall(sequence):
		for i in nom.findall(sequence):
			CG_nb = CG_nb + 1

	# fragment number
	fragments_number = fragments_number + 1

	# RR genome length
	RR_genome_size = RR_genome_size + len(sequence)

	return CG_nb, fragments_number, RR_genome_size


def genome_parameters(filename_with_path):

	sequence =''
	fragments_number = 0
	CG_total_nb = 0
	fragments_total_number = 0
	RR_genome_total_size = 0

	RR_genome_size = 0
	fragments_number = 0
	CG_nb = 0


	if filename_with_path == argv[2]:
		filetype = 'genome'
	else:
		filetype = 'RR_genome'
	

	ifh = open(filename_with_path)

	for line in ifh:
		line = line.rstrip('\r\n')
		if line.startswith('>'):
			if sequence !='':

				values = counts(filetype,sequence, rest_site, CG_nb, fragments_number, RR_genome_size)
				CG_total_nb = values[0] + CG_total_nb
				fragments_total_number = values[1] + fragments_total_number
				RR_genome_total_size = values[2] + RR_genome_total_size

			sequence =''
		     
		else:
	
			line = line.upper()

			if re.match ('^[AGTCN]*$', line):
				sequence=sequence+line
			else:
				print 'found non-DNA caracters in the sequence', line
		

	if sequence !='':
	
		values = counts(filetype,sequence, rest_site, CG_nb, fragments_number, RR_genome_size)
		CG_total_nb = values[0] + CG_total_nb
		fragments_total_number = values[1] + fragments_total_number
		RR_genome_total_size = values[2] + RR_genome_total_size


		# total fragment number
		fragments_number = fragments_number + 1

	
	ifh.close()


	return RR_genome_total_size, CG_total_nb,fragments_total_number



filename_with_path = argv[1] 
genome_with_path = argv[2]
rest_site = argv[3]



RR_genome_total_size,CG_total_nb,fragments_total_number = genome_parameters(filename_with_path)

genome_total_size,genome_CG_number,chromosomes_total_number = genome_parameters(genome_with_path)


output_file = os.path.basename(filename_with_path) + "_results" + ".txt"
ofh = open(output_file, "w")  
ofh.write("Sample"+'\t'+"RR genome size"+'\t'+"% of whole genome"+'\t'+"number of fragments"+'\t'+"number of CpG sites (RR genome)"+'\t'+"% of total genomic CpG sites"+'\n')

ofh.write(os.path.basename(filename_with_path)+'\t'+str(RR_genome_total_size)+'\t')




pct_whole_genome = (RR_genome_total_size/float(genome_total_size))*100
pct_CG_whole_genome = (CG_total_nb/float(genome_CG_number))*100

pct_whole_genome = round(pct_whole_genome,1)
pct_CG_whole_genome = round(pct_CG_whole_genome,1)

ofh.write(str(pct_whole_genome)+'\t'+ str(fragments_total_number)+'\t'+ str(CG_total_nb) +'\t'+ str(pct_CG_whole_genome) +'\n')

ofh.close()


