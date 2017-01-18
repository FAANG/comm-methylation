#----------------------------------------------------------------
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
#----------------------------------------------------------------
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
Usage:
./parse_extract.py sample_directory

input : output from Bismark methylation extractor 
Sample_X/extract/CpG_context_Sample_X_R1_val_1.fq_bismark_pe.txt
HWI-D00629:44:C6KV1ANXX:1:1101:1465:1913_1:N:0:AGGTAC   -       2       88462987        z

output : % of methylated cytosines for each cpg position 
Chromosome      Position        Coverage        # methylated    % methylated
1       20108   4       4       100

"""

from string import *
from sys import argv
import re
import os
from os import getcwd

########################
debug=0
########################

dir_data=argv[1]

fastq_dir = dir_data + '/trim_galore/'

for fastq_file in os.listdir(fastq_dir):
	pattern = re.search("_R1_trimmed.fq(.gz)?",fastq_file)
	pattern2 = re.search("_R1_val_1.fq(.gz)?",fastq_file)
	if pattern:
		fastq_file_se = fastq_file
		file_cpg_single_end = dir_data +  '/extract/' + 'CpG_context_' + fastq_file_se + '_bismark.txt'
		
		if os.path.exists(file_cpg_single_end):
			#print 'ok single end'
			file_cpg = file_cpg_single_end


	elif pattern2:
		fastq_file_pe = fastq_file
		file_cpg_paired_end = dir_data +  '/extract/' + 'CpG_context_' + fastq_file_pe + '_bismark_pe.txt'

		if os.path.exists(file_cpg_paired_end):
			#print 'ok paired end'
			file_cpg = file_cpg_paired_end



open_file_cpg = open(file_cpg)
	
cpg_context = {}

noLine=1
for line in open_file_cpg:

	if line.startswith('Bismark methylation extractor'):
		continue
	
	noLine=noLine+1
	if debug==1 and noLine>100000:
		break

	line = line.rstrip('\n\r')
	elmts = line.split()
	# ['HWI-D00629:44:C6KV1ANXX:1:1101:6022:3658_1:N:0:AGGTAC', '-', '9', '29828', 'x']
	read , sens , chromosome , cpg_position , cpg_call = elmts
	
	if chromosome.startswith('chr'):
		search_chr = re.search('chr(.*)',chromosome)
		chromosome = search_chr.group(1)

	if re.match("^[0-9]", chromosome):
		chromosome = int(chromosome)

	cpg_position = int(cpg_position)

# data are added in a dictionnary :
# cpg_context[chromosome][CpGPosition][contexte]

	if not chromosome in cpg_context:
		cpg_context[chromosome] = {}

	if not cpg_position in cpg_context[chromosome]:
		cpg_context[chromosome][cpg_position] = {}
	if not cpg_call in cpg_context[chromosome][cpg_position]:
		cpg_context[chromosome][cpg_position][cpg_call] = 0

	cpg_context[chromosome][cpg_position][cpg_call]+=1
	

open_file_cpg.close()


# data processing #

methylations = {}

for chromosome in cpg_context:
	for cpg_position in cpg_context[chromosome]:

		cpg_call = 'Z'
		cpg_call_lett_min = lower(cpg_call)
		nb_Z = 0
		nb_z = 0
		if cpg_call in cpg_context[chromosome][cpg_position]:
			if cpg_call_lett_min in cpg_context[chromosome][cpg_position]:
				nb_Z = cpg_context[chromosome][cpg_position][cpg_call]
				nb_z = cpg_context[chromosome][cpg_position][cpg_call_lett_min]
			else :
				# only reads in context 'Z'
				nb_Z = cpg_context[chromosome][cpg_position][cpg_call]
		else:
			if cpg_call_lett_min in cpg_context[chromosome][cpg_position]:
			# only reads in context 'h'
				nb_z = cpg_context[chromosome][cpg_position][cpg_call_lett_min]

		if nb_Z != 0 or nb_z != 0 :
			if not chromosome in methylations:
				methylations[chromosome] = {}
			if not cpg_position in methylations[chromosome]:
				methylations[chromosome][int(cpg_position)] = {}	
			methylation_coverage = nb_Z + nb_z
			methylations[chromosome][int(cpg_position)] = (methylation_coverage , nb_Z)




#Filter for consecutive positions
toSkip= {} 
for chromosome in sorted(methylations):
	for cpgPosition in sorted(methylations[chromosome]):
		#print "cpgPosition="+str(cpgPosition)
		if (int(cpgPosition)+1) in methylations[chromosome]:
			#print ""+str(cpgPosition)+" consecutive"
			methylation_coverage1 , nb_Z1 = methylations[chromosome][int(cpgPosition)]
			methylation_coverage2 , nb_Z2 = methylations[chromosome][int(cpgPosition+1)]
			methylations[chromosome][int(cpgPosition)]=(methylation_coverage1+methylation_coverage2, nb_Z1+nb_Z2)
			if not chromosome in toSkip:
				toSkip[chromosome] = {}
			toSkip[chromosome][cpgPosition+1]=1
	


# Sorting and display of the results
context = 'Z'

output_path = dir_data +  '/extract/' 
ofh  = open(output_path + "synthese_CpG.txt", "w") 

ofh_BED10  = open(output_path +'coverage_10.bedGraph','w')

ofh_BED5  = open(output_path +'coverage_5.bedGraph','w')

ofh.write('Chromosome' + '\t'+ 'Position' + '\t' +  'Coverage'     + '\t' +   '# methylated' + '\t' + '% methylated' + '\n')


for chromosome in sorted(methylations):
	for cpgPosition in sorted(methylations[chromosome]):
			
			if toSkip and chromosome in toSkip and cpgPosition in toSkip[chromosome]:
				#print 'consecutive positions at ',chromosome,":",cpgPosition
				continue
			meth = methylations[chromosome][int(cpgPosition)]
			methylation_coverage , nb_Z = meth
			methylation_percent = round(nb_Z / float(methylation_coverage)*100,1)
			methylation_percent = str(methylation_percent)
			pattern4 = re.search("\.0$",methylation_percent)
			if pattern4:
				methylation_percent = re.sub("\.0","",methylation_percent)
			

			ofh.write(str(chromosome) + '\t' + str(cpgPosition) + '\t' + str(methylation_coverage) + '\t' + str(nb_Z) + '\t' + methylation_percent + '\n')
			if methylation_coverage >= 5:

				ofh_BED5.write( str(chromosome) + '\t' + str(cpgPosition) + '\t' +  str(cpgPosition+1) + '\t' + str(float(methylation_percent)/100) + '\n')

			if methylation_coverage >= 10:
				ofh_BED10.write( str(chromosome) + '\t' + str(cpgPosition) + '\t' +  str(cpgPosition+1) + '\t' + str(float(methylation_percent)/100) + '\n')



ofh.close()
ofh_BED5.close()
ofh_BED10.close()
