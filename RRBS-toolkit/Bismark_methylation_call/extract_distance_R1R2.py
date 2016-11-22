
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

