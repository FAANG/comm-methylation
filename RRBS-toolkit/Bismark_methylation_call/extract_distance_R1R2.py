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

import sys
import os
from string import *
from sys import argv
import re


"""
Input : Bam file from Sample/bismark

Output : txt file

Distance
-84
84
-45
45
-1
1
1

"""

# relative path of the main directory containing the data
dir_data=argv[1]
# ../test_FP_paired_end

# relative path of the bam file
bam_file=argv[2]
# ../test_FP_paired_end/bismark/test_FP_paired_end_R1_val_1.fq_bismark_pe.bam

# name of the bam file
bam_file_name = os.path.basename(bam_file)

# change file name suffix from .bam to .sam (file name only)
pattern4 = re.search(".bam$",bam_file_name)
if pattern4:
	sam_file = re.sub(".bam",".sam",bam_file_name)


# os.path.abspath(bam_file) = absolute path of the bam file

# absolute directory name of the .bam file
dir_name_file = os.path.dirname(os.path.abspath(bam_file))


pattern = re.search(".bam$",bam_file_name)
if pattern:

	cmd = os.environ['SAMTOOLS_EXECUTE']+ ' view ' + '-h -o ' + dir_name_file + '/' + sam_file + ' ' + os.path.abspath(bam_file)
	os.system(cmd)

else:
	print "No bam file in the data directory"
	sys.exit(1)



ifh = open(dir_name_file + '/' + sam_file)


try:
	ofh = open(dir_data + "/extract/distance_R1R2.txt", "w")   

except IOError:
	sys.exit(1)

ofh.write("Distance\n")

while 1:
	line = ifh.readline()
	if not line:
		break

	if line.startswith('@'):
		continue

	line = line.rstrip('\n\r')

	elmts = line.split('\t')

	read=elmts[0]
	chr1=elmts[2]
	start1 = int(elmts[3])
	chr2=elmts[6]
	start2 = int(elmts[7])

	if chr2 != "=" and chr1 != chr2:
		continue
	dist = start2-start1
	ofh.write(str(dist)+"\n")


ifh.close()
ofh.close()

