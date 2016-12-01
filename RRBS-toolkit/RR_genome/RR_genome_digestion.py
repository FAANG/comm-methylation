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
Produce a Reduced Representation genome from fasta file genome . The sequence is cut into fragments according to the given restriction enzyme recognition sequence : This sequence is always cleaved just after the 5prime first base towards 3prime and just before the last base on the complementary strand

ex for Msp1: 

     C|CGG
       --
     GGC|C

ex for BssS1:

	C|ACGAG
          ----
        GTGCT|C

Fragments are size selected or not. Chromosomes scaffolds can be treated or not.

The output is a fragment fasta file that is chromosome sorted. The description line displays the chromosome name, fragment start and stop. 

CG addition : the Python split comand causes the disappearance of all CCGG in the sequences. Then we have to add CCG, CGG and C in the fragments. CGG is always added at the 5' start of the fragments (except for the first one). A C is always added at the 3' end of the fragments. A CG is added to the C at the 3' end of the fragments ONLY if the following fragment is not contiguous.
 
argument #1 = fasta file genome (sequences must be written on one line only)

argument #2 = recognition sequence (ie : CCGG for Msp1)

argument #3 = min fragment size, argument #4 = max fragment size (if min = 0 and max = -1, no size selection)

argument #5 = enter "1" if chromosomes scaffolds must be treated

"""
from string import *
from sys import argv
import re
import os
from os import getcwd


########## FUNCTIONS

def cut_seq(sequence,rest_enz,fragment_number,empty_fragments):
	coupage_seq = sequence.split(rest_enz)
	start_frag = 1
	end_frag = 0

	for idx in range(0,len(coupage_seq)):
		# fragment count incremented
		####fragment_number = fragment_number + 1
		current_frag = coupage_seq[idx] 

		if current_frag == '':
		# if frag is empty, empty frag incremented
			empty_fragments = empty_fragments + 1

		# if not the first fragment:
		if idx != 0:
			current_frag = rest_enz[1:]+ current_frag # CGG for Msp1

		sel_current_frag = 0
		if max_frag == -1 or (len(current_frag) > int(min_frag) and len(current_frag) < int(max_frag)):
			sel_current_frag = 1

		# If not the first fragment:
		if idx != 0:
			# if current_frag has the right size
			if sel_current_frag == 1:
					# if the precedent fragment has the right size
				if sel_last_frag == 1:
					# => contigous fragments 
					last_frag = last_frag + rest_enz[:-3] #C
					
				else: # if the precedent fragment hasn't the right size
					last_frag=last_frag + rest_enz[:-1] #CCG
						
						# end If sel_last_frag == 1:

			else:     # If sel_last_frag != 1 & If sel_current_frag != 1:
				last_frag = last_frag + rest_enz[:-1] #CCG

					# End if sel_current_frag == 1:

			if sel_last_frag == 1:
				ofh.write(chromosome +'\t'+ str(start_frag) + '\t'+ str(end_frag) + '\t'+ last_frag + '\n')
				fragment_number = fragment_number + 1
				# End if sel_last_frag == 1:
			# End if not first fragment:

		# precedent fragment becomes the selected one
		sel_last_frag = sel_current_frag
			# the first fragment becomes the last treated one
		last_frag = current_frag
		start_frag = end_frag + 1
		end_frag = len(current_frag) + start_frag


	# END for idx in........
	if sel_last_frag:
		ofh.write(chromosome +'\t'+ str(start_frag) + '\t'+ str(end_frag) + '\t'+ last_frag +'\n')
		fragment_number = fragment_number + 1
	return fragment_number, empty_fragments





################ arguments recall

# genome fasta file
input_file = argv[1]

# restriction enzyme recognition sequence
rest_enz = argv[2]

# min fragment size
min_frag = int(argv[3])

# max fragment size : if = -1 no size selection
max_frag = int(argv[4])


if len(argv)>=6:
	treat_scaffold=int(argv[5])
else:
	treat_scaffold=0

if treat_scaffold!=1 and treat_scaffold!=0:
	print "Treat scaffold parameter incorrect (expect 1 or 0) : ",treat_scaffold
	exit(1)


##################### arguments recall
print "---------------------------"
print "Input file :\t",input_file
print "Restriction site :\t",rest_enz

if max_frag==-1:
	label_selection="No selection"
	output_file1=os.path.abspath(input_file)
	output_file1=output_file1[:(output_file1.rfind("."))]+"_frag_in_silico_"+rest_enz+".tmp"

	output_file2=os.path.abspath(input_file)
	output_file2=output_file2[:(output_file2.rfind("."))]+"_frag_in_silico_"+rest_enz+".fasta"
else:
	label_selection="[" + str(min_frag) + ";" + str(max_frag) +"]"
	output_file1=os.path.abspath(input_file)
	output_file1=output_file1[:(output_file1.rfind("."))]+"_frag_in_silico_"+rest_enz+"_"+str(min_frag)+"_"+str(max_frag)+".tmp"
	
	output_file2=os.path.abspath(input_file)
	output_file2=output_file2[:(output_file2.rfind("."))]+"_frag_in_silico_"+rest_enz+"_"+str(min_frag)+"_"+str(max_frag)+".fasta"

print "Size selection :\t",label_selection
if treat_scaffold==0:
	label_scaffold="No"
else:
	label_scaffold="Yes"
print "Treat scaffold :\t",label_scaffold
print "Output file :\t",output_file2
print "---------------------------"




############# Variables

Fragment_total_number = 0
fragment_number = 0
empty_fragments = 0
empty_fragments_total_number = 0
sequence =''
numericChromosome=re.compile('([Cc][Hh][Rr])?([0-9]+)$')
realChromosome=re.compile('([Cc][Hh][Rr])?(M[Tt]|X|Y)$')



#######################################################################################
current_dir = getcwd()

ifh = open(os.path.abspath(input_file))

pattern = re.search(".fa$",input_file)
if pattern:
	input_file = re.sub(".fa$","",input_file)

ofh  = open(output_file1, "w") 

for line in ifh:
	line = line.rstrip('\r\n')
	if line.startswith('>'):
		if sequence !='':
			output_var_from_cut_seq_function = cut_seq(sequence,rest_enz,fragment_number,empty_fragments)
			Fragment_total_number = Fragment_total_number + output_var_from_cut_seq_function[0]
			empty_fragments_total_number = empty_fragments_total_number + output_var_from_cut_seq_function[1]

		line = line.split()

		chromosome = line[0]
		pattern_chr = re.search("^>([Cc][Hh][Rr])?_?(.*)$",chromosome)
		if pattern_chr: 
			chromosome = pattern_chr.group(2)

		sequence =''

		# scaffolds are not treated: chrUn....
		toTreat=0
		if (numericChromosome.match(chromosome) or realChromosome.match(chromosome) or treat_scaffold==1):
			toTreat=1
		     
	else:
		if toTreat==0:
			continue

		line = line.upper()
		# Test if line matching (^[AGTCN]*$ ) if non return error
		if re.match ('^[AGTCN]*$', line):
			sequence=sequence+line
		else:
			print 'caracteres speciaux trouves', line
		
	# End if line starts with >



if sequence !='':
# last fragment to treat

	output_var_from_cut_seq_function = cut_seq(sequence,rest_enz,fragment_number,empty_fragments)
	Fragment_total_number = Fragment_total_number + output_var_from_cut_seq_function[0]
	empty_fragments_total_number = empty_fragments_total_number + output_var_from_cut_seq_function[1]

#FinSi

print "Fragments total number = ", Fragment_total_number
print 'Empty fragments total number = ', empty_fragments_total_number

ifh.close()
ofh.close()



########## SORTING Chromosomes

file_1 = open(output_file1)
ofh = open(output_file2, "w")  

locations={}

print "Sorting initialization..."
for line in file_1:
	line = line.rstrip('\n\r')
	elmts = line.split("\t")
	chr = elmts[0]
	start = elmts[1]
	end = elmts[2]
	sequ = elmts[3]
	keyLoc = chr + "_"+ start+ "_"+ end
	if locations.has_key(keyLoc):
		print "Several lines for chromosome '",chr,"' and start=",start
	locations[keyLoc]=sequ


file_1.close()

#print locations

def sortChromosomeAndStart_V2(keyLoc1, keyLoc2):

	# split the keyloc with regards to the underscore between the chromosome and the start

	m1=re.match("^(.*)_([0-9]+)_([0-9]+)$",keyLoc1)
	if m1 is None :
		sys.exit("Cannot interpret chromosome location '"+keyLoc1+"'. Exiting.")

	m2=re.match("^(.*)_([0-9]+)_([0-9]+)$",keyLoc2)
	if m2 is None :
		sys.exit("Cannot interpret chromosome location '"+keyLoc2+"'. Exiting.")

	loc1 = (m1.group(1),m1.group(2))
	loc2 = (m2.group(1),m2.group(2))

	if (loc1[0] == loc2[0]):
		# if same chromosome : sort on start
		return int(loc1[1])-int(loc2[1])
	else:
		m = numericChromosome.match(loc1[0])
		if m:
			# group : return the string matched by the RE
			chr1 = m.group(2)
			m = numericChromosome.match(loc2[0])
			if m:
				chr2 = m.group(2)
				#Compare chromosome number
				return int(chr1)-int(chr2)
				
			else:
				return -1
		else:
			m = numericChromosome.match(loc2[0])
			if m:
				return 1
			else: #Neither chr1 nor chr2 are numeric
			      
				m1 = realChromosome.match(loc1[0])
				m2 = realChromosome.match(loc2[0])
				if m1 and m2:
					if loc1[0] < loc2[0]:
						return -1
					else:
						return 1
				elif m1:
					return -1
				elif m2:
					return 1
				else:
					#Compare letters
					if loc1[0] < loc2[0]:
						return -1
					else:
						return 1


sortedLocations = sorted(locations.keys(), cmp = sortChromosomeAndStart_V2)

for keyLoc in sortedLocations:

	ofh.write('>' + keyLoc + '\n' + locations[keyLoc] + '\n')


os.chmod(output_file2, 0775)
os.remove(output_file1)
ofh.close()
