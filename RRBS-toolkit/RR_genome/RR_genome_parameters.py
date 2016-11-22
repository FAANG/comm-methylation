
"""

# Parse the output of "dig_genome_RRBS.py" (RR fragments fasta file)

# Output 
total length of the fragments (RR genome size)
number of fragments
number of CG

remove the bases added by the "dig_genome_RRBS.py" script at the end of the fragment according to the used restriction enzyme. Here only Msp1, XmaC1 or BssS1 can be used.

requires a genome species : rabbit, bovine and pig are available


# Command line = ./RR_genome_parametres.py   <fragments_fasta_file.fa> <genome species> <restriction site recognition sequence ("CCGG" or "CCCGGG" or "CACGAG" or "0")>

# Output file = "stats_fragments_fasta_file.txt"

"""

from string import *
from sys import argv
import sys
import re
import os, stat

#########
debug = 1
#########

######## FUNCTIONS
def counts(sequence, rest_site, CG_nb, fragments_number, RR_genome_size):

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



######## VARIABLES
# rabbit genome data:		
genome_size = {
	"rabbit":	2737490501.0,
	"bovine":	2670422299.0,
	"pig":		2808525831.0,
	"mouse":	1.0,
	"test":         1.0
}
genome_CG_number = {
	"rabbit":	36000387.0,
	"bovine":	27540367.0,
	"pig":		30460432.0,
	"mouse":	1.0,
	"test":         1.0
}

sequence =''
RR_genome_size = 0
RR_genome_total_size = 0
fragments_number = 0
fragments_total_number = 0
CG_nb = 0
CG_total_nb = 0



######## 
filename = argv[1] 
rest_site = argv[2]

pattern = re.search("\.\./Genomes/([a-zA-Z0-9_]+)/[a-zA-Z0-9._]+.fa[s]?[t]?[a]?$",filename)

if pattern:
	genome_name = pattern.group(1)
else:
	print "species not defined!!!"

genome_name = genome_name.lower()

if genome_name == "rabbit" or genome_name == "bovine" or genome_name == "pig" or genome_name == "test" or genome_name == "mouse":

	ifh = open(filename)
	output_file = filename + "_results" + ".txt"

	ofh = open(output_file, "w")   

	for line in ifh:
		line = line.rstrip('\r\n')
		if line.startswith('>'):
			if sequence !='':

				values = counts(sequence, rest_site, CG_nb, fragments_number, RR_genome_size)
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
	
		values = counts(sequence, rest_site, CG_nb, fragments_number, RR_genome_size)
		CG_total_nb = values[0] + CG_total_nb
		fragments_total_number = values[1] + fragments_total_number
		RR_genome_total_size = values[2] + RR_genome_total_size

		if debug == 0:
			print "RR_genome_size : ",RR_genome_total_size

		# total fragment number
		fragments_number = fragments_number + 1

		if debug == 0:
			print "fragments_number : ",fragments_total_number

		#output file title line
		ofh.write("Sample"+'\t'+"RR genome size"+'\t'+"% of whole genome"+'\t'+"number of fragments"+'\t'+"number of CpG sites (RR genome)"+'\t'+"% of total genomic CpG sites"+'\n')

		ofh.write(filename+'\t'+str(RR_genome_total_size)+'\t')


	pct_whole_genome = (RR_genome_total_size/genome_size[genome_name])*100
	pct_CG_whole_genome = (CG_total_nb/genome_CG_number[genome_name])*100

	pct_whole_genome = round(pct_whole_genome,1)
	pct_CG_whole_genome = round(pct_CG_whole_genome,1)

	ofh.write(str(pct_whole_genome)+'\t'+ str(fragments_total_number)+'\t'+ str(CG_total_nb) +'\t'+ str(pct_CG_whole_genome) +'\n')

	ifh.close()
	ofh.close()


else :
	print "Species must be 'rabbit', 'bovine', 'mouse' or 'pig'"
	sys.exit(1)





