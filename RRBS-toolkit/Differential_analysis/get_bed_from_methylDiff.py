import os
import re
import sys
from sys import argv

###################
debug=0;
###################

config_file=argv[1];
log_file=argv[2];

step2file={}
try :
	in_file=open(log_file,"rt")
	for line in in_file.readlines():
		line=line.rstrip("\n")
		me=re.match("^CMD (.*)$",line)
		if me is not None:
			step=me.group(1)
			continue
		me=re.match("^OUT (.*)$",line)
		if me is not None:
			file_in=me.group(1)
			step2file[step]=file_in
	in_file.close()
except IOError as exc:
	sys.exit("Cannot open log file '{0}' : {1}".format(log_file,exc))

file_in=step2file["get_diff_methyl.R"];


#####################
## Default values
#####################
stat_value="pvalue";
stat_threshold1=0.01;
stat_threshold2=0.05;
output_dir=".";

try :
	in_file=open(config_file,"rt")
	for line in in_file.readlines():
		line=line.rstrip("\n")
		me=re.match("^#stat_value\t([^#]*)(#.*)?$",line)
		if me is not None:
			stat_value=me.group(1)
			continue
		me=re.match("^#stat_threshold1\t([^#]*)(#.*)?$",line)
		if me is not None:
			stat_threshold1=float(me.group(1))
			continue
		me=re.match("^#stat_threshold2\t([^#]*)(#.*)?$",line)
		if me is not None:
			stat_threshold2=float(me.group(1))
			continue
		me=re.match("^#output_dir\t([^#]*)(#.*)?$",line)
		if me is not None:
			output_dir=me.group(1)
			continue
	in_file.close()
except IOError as exc:
	sys.exit("Cannot open config file '{0}' : {1}".format(config_file,exc))

try:
	out_log=open(log_file,"at")
	out_log.write("CMD get_bed_from_methyl.py\n")
	out_log.write("\tConfiguration file :\n")
	out_log.write("\t--------------------\n")
	out_log.write("\t\tstat.value="+stat_value+"\n")
	out_log.write("\t\tstat1.threshold="+str(stat_threshold1)+"\n")
	out_log.write("\t\tstat2.threshold="+str(stat_threshold2)+"\n")
	out_log.write("\t\toutput.dir="+output_dir+"\n")
	out_log.close()
except IOError as exc:
	sys.exit("Cannot open config file '{0}' : {1}".format(config_file,exc))

bed2_file=file_in.replace(".txt",".bed")
bed1_file=bed2_file.replace(stat_value+str(stat_threshold2),stat_value+str(stat_threshold1))

try :
	in_file=open(file_in,"rt")
	out_bed1=open(bed1_file,"wt")
	out_bed2=open(bed2_file,"wt")
	no_line=0
	for line in in_file.readlines():
		line=line.rstrip("\n")

		no_line+=1
		if no_line==1:
			continue

		elmts=line.split("\t")
		chr=elmts[0]
		pos=elmts[1]
		value=float(elmts[-2])
		if value < stat_threshold1:
			out_bed1.write(chr+"\t"+pos+"\t"+str(int(pos)+1)+"\t"+"\n")
		if value < stat_threshold2:
			out_bed2.write(chr+"\t"+pos+"\t"+str(int(pos)+1)+"\t"+"\n")
	
	in_file.close()
	out_bed1.close()
	out_bed2.close()
		
except IOError as exc:
	sys.exit("Cannot create bed file from input file '{0}' : {1}".format(file_in,exc))

