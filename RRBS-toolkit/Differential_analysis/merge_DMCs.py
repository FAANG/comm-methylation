#
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
#


import os
import re
import sys
from sys import argv


### Sort CpG 'chr.position' by chromosome then position
def CpG_compare(x, y):
	CpG1=x.split(".")
	CpG2=y.split(".")
	if (CpG1[0] == CpG2[0]):
		#Meme chromosome : on compare numeriquement les coordonnees
		return int(float(CpG1[1])) - int(float(CpG2[1]))
	else:
		#Les chromosomes sont dfifferents : on les compare
		chr1_is_num=re.match("^[0-9]+$",CpG1[0])
		chr2_is_num=re.match("^[0-9]+$",CpG2[0])
		if chr1_is_num!=None and chr2_is_num!=None:
			#Les 2 chromosomes sont numeriques : on les compare numeriquement
			return int(float(CpG1[0])) - int(float(CpG2[0]))
		elif chr1_is_num!=None:
			#Seule le chromosome 1 est numerique
			return -1
		elif chr2_is_num!=None:
			#Seule le chromosome 2 est numerique
			return +1
		else:
			#Les 2 chromosomes ne sont pas numeriques : on les compare sous forme de chaines
			if CpG1[0].__lt__(CpG2[0]):
				return -1
			else:
				return +1


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
		me=re.match("^#stat_method\t([^#]*)(#.*)?$",line)
		if me is not None:
			stat_method=me.group(1)
			continue
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
	out_log.write("CMD merge_DMCs.py\n")
	out_log.write("\tConfiguration file :\n")
	out_log.write("\t--------------------\n")
	out_log.write("\t\tstat.value="+stat_value+"\n")
	out_log.write("\t\tstat1.threshold="+str(stat_threshold1)+"\n")
	out_log.write("\t\tstat2.threshold="+str(stat_threshold2)+"\n")
	out_log.write("\t\toutput.dir="+output_dir+"\n")

	CpGs={}

	#Read statistical results
	if "get_diff_methyl.R" not in step2file:
		sys.exit("No output file defined fo statistical step. Exiting.")

	stat_file=step2file["get_diff_methyl.R"];
	in_stat=open(stat_file,"rt")

	no_line=0	
	field2pos={}
	for line in in_stat.readlines():
		no_line+=1
		line=line.rstrip("\n")
		elmts=line.split("\t")
		if no_line==1:
			header_stat=line
			pos=0
			for field in elmts:
				field2pos[field]=pos
				pos+=1
			if stat_value not in field2pos:
				sys.exit("No '"+stat_value+"' field found in header of '"+stat_file+"'.")
			continue
		pq_value=float(elmts[field2pos[stat_value]])
		if pq_value > stat_threshold1:
			continue
		id=elmts[0]+"."+elmts[1]
		CpGs[id]=line
	in_stat.close()

	#Read obvious results
	nb_obvious_added=0
	if "get_obvious_DMC.py" not in step2file:
		sys.exit("No output file defined for obvious DMCs discovery step. Exiting.")

	obvious_file=step2file["get_obvious_DMC.py"];
	in_obvious=open(obvious_file,"rt")

	no_line=0
	field2pos={}
	for line in in_obvious.readlines():
		no_line+=1
		line=line.rstrip("\n")
		elmts=line.split("\t")
		if no_line==1:
			#Add pValue/qValue field before last field
			idx=len(elmts)-1
			elmts.append(elmts[idx])
			elmts[idx]=elmts[idx-1]
			elmts[idx-1]=stat_value
			header_obvious="\t".join(elmts)
			if header_obvious != header_stat:
				print "header stat:\n'"+header_stat+"'\n"
				print "header obvious:\n'"+header_obvious+"'\n"
				sys.exit("Order of samples in '"+stat_file+"' and '"+obvious_file+"' differs. Exiting.")
			continue
		id=elmts[0]+"."+elmts[1]
		if id not in CpGs:
			#Add pValue/qValue field before last field
			idx=len(elmts)-1
			elmts.append(elmts[idx])
			elmts[idx]=elmts[idx-1]
			elmts[idx-1]=""
			line="\t".join(elmts)
			CpGs[id]=line
			nb_obvious_added+=1
	in_stat.close()

	#Output
	txt_out=step2file["get_diff_methyl.R"].replace(".txt"," - with obvious DMCs.txt")
	txt_out=txt_out.replace(stat_value+str(stat_threshold2),stat_value+str(stat_threshold1))
	out_txt=open(txt_out,"wt")
	out_txt.write(header_stat+"\n")

	bed_out=txt_out.replace(".txt",".bed")
	out_bed=open(bed_out,"wt")

	for pos in sorted(CpGs.keys(), cmp=CpG_compare):
		out_txt.write(CpGs[pos]+"\n")
		me=re.match("^(.*)[.]([0-9]+)$",pos)
		if me is None:
			sys.exit("Cannot interpret CpG position '"+pos+"'. Exiting.")
		chr=me.group(1)
		pos=int(float(me.group(2)))
		out_bed.write(chr+"\t"+str(pos)+"\t"+str(pos+1)+"\n")
	out_txt.close()
	out_bed.close()

	out_log.write("INFO number of obvious CpGs added to "+stat_method+"="+str(nb_obvious_added)+"\n")
	out_log.write("OUT "+txt_out+"\n")
	out_log.close()

except IOError as exc:
	sys.exit("Cannot append to log file '{0}' : {1}".format(log_file,exc))
