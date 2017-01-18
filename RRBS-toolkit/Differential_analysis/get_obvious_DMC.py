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

import os
import re
import sys
from sys import argv

config_file=argv[1];
log_file=argv[2];

#####################
## Default values
#####################
min_coverage=10;
max_coverage=-1;
pct_threshold=100;
output_dir=".";
title=""

if not os.path.isfile(config_file) :
	sys.exit("Unable to find configuration file for getObviousDMCs : '"+config_file+"'")

try :
	reference_cond=alternative_cond=""
	files=[];
	samples=[];
	cond2samples={}
	sample2cond={}
	file2smp={}
	state=0;
	no_file=0;
	in_file=open(config_file,"rt")
	for line in in_file.readlines():
		line=line.rstrip("\n")
		me=re.match("^#min_coverage2\t([^#]*)(#.*)?$",line)
		if me is not None:
			min_coverage=int(me.group(1))
			continue
		me=re.match("^#max_coverage2\t([^#]*)(#.*)?$",line)
		if me is not None:
			max_coverage=int(me.group(1))
			continue
		me=re.match("^#methdiff_threshold2\t([^#]*)(#.*)?$",line)
		if me is not None:
			pct_threshold=float(me.group(1))
			if pct_threshold <= 1 :
				pct_threshold = pct_threshold * 100
			continue
		me=re.match("^#output_dir\t([^#]*)(#.*)?$",line)
		if me is not None:
			output_dir=me.group(1)
			continue
		me=re.match("^#title\t([^#]*)(#.*)?$",line)
		if me is not None:
			title=me.group(1)
			continue
		if re.match("^Sample\t.*$",line):
			state=1
			continue
		if state == 0:
			continue
		elmts=line.split("\t")
		smp=elmts[0]
		file=elmts[1]
		cond=elmts[2]
		if reference_cond == "":
			reference_cond=cond
		if alternative_cond == "" and cond != reference_cond:
			alternative_cond=cond

		if cond not in cond2samples:
			cond2samples[cond]=""
		else:
			cond2samples[cond]+="\t"
		cond2samples[cond]+=smp
		sample2cond[smp]=cond

		file2smp[file]=smp
		files.append(file)
		samples.append(smp)
		
	in_file.close()
except IOError as exc:
	sys.exit("Cannot open config file '{0}' : {1}".format(config_file,exc))

try :
	out_log=open(log_file,"at")
	out_log.write("CMD get_obvious_DMC.py\n")

	out_log.write("\tConfiguration file :\n")
	out_log.write("\t--------------------\n")
	out_log.write("\t\tmin_coverage2="+str(min_coverage)+"\n")
	if max_coverage != -1 :
		out_log.write("\t\tmax_coverage2="+str(max_coverage)+"\n")
	else :
		out_log.write("\t\tmax_coverage2= no limit\n")

	out_log.write("\t\tmethdiff_threshold2="+str(pct_threshold)+"\n")

	coverages={}
	occurrences_C={}
	methyl={}
	for file in files:
		smp=file2smp[file]
		out_log.write("\tReading "+smp+" ...\n")
		try :
			in_file=open(file,"rt")
			no_line=0
			for line in in_file.readlines():
				line=line.rstrip("\n")
				no_line+=1
				if no_line==1:
					continue
				elmts=line.split("\t")
				id=elmts[0]+"."+elmts[1]
				coverage=int(elmts[2])
				if coverage<min_coverage or (max_coverage!=-1 and coverage>max_coverage) :
					continue

				freq_C=float(elmts[-1])
				main="";
				if freq_C>=pct_threshold :
					main="C"
				elif freq_C<=100-pct_threshold :
					main="T"
				
				if main == "":
					continue
				if id not in coverages:
					coverages[id]={}
					occurrences_C[id]={}
					methyl[id]={}

				coverages[id][smp]=coverage
				occurrences_C[id][smp]=int(freq_C*coverage/100.0)
				methyl[id][smp]=main
				

			in_file.close()

		except IOError as exc:
			sys.exit("Cannot open input file '{0}' : {1}".format(file,exc))

	final={}
	for id in methyl.keys():
		nb_OK=nb_samples=0

		for smp in samples:
			if smp in methyl[id]:
				nb_OK+=1
			nb_samples+=1
		if nb_OK!=nb_samples:
			continue
		values={}
		avg_occurrences_C={}
		tot_coverage={}
		nb_cond_ok=0
		for cond in cond2samples.keys():
			nb_OK=nb_samples=0
			avg_occurrences_C[cond]=0
			tot_coverage[cond]=0
			for smp in cond2samples[cond].split("\t"):
				if cond not in values:
					values[cond]=methyl[id][smp]
					nb_OK=1
				else:
					if values[cond] == methyl[id][smp]: #Same FC
						nb_OK+=1
				nb_samples+=1
				if smp in coverages[id]:
					avg_occurrences_C[cond]+=occurrences_C[id][smp]
					tot_coverage[cond]+=coverages[id][smp]

			avg_occurrences_C[cond]/=tot_coverage[cond]
			avg_occurrences_C[cond]*=100.0
			if nb_OK==nb_samples:
				nb_cond_ok+=1
	
		if nb_cond_ok!=2:
			continue

		conds=cond2samples.keys()
		if values[conds[0]] == values[conds[1]]:
			continue
		me=re.match("^(.*)[.]([0-9]+)$",id)
		if me is None:
			sys.exit("Cannot interpret CpG position '"+id+"'. Exiting.")
		chr=me.group(1)
		start=int(me.group(2))
		smp=samples[0]
		if chr not in final:
			final[chr]={}

		final[chr][start]=avg_occurrences_C[reference_cond]-avg_occurrences_C[alternative_cond]

	#Output
	if title== "" :
		title=",".join(cond2samples[reference_cond].split("\t")) + "_" + \
		      ",".join(cond2samples[alternative_cond].split("\t"))

	txt_out=output_dir+"/obvious_DMCs_"+ \
		title + "_mincov"+str(min_coverage)

	if max_coverage != -1 :
		txt_out+="_maxcov"+str(max_coverage)

	txt_out+= "_threshold"+str(pct_threshold)+ \
		  ".txt"
	bed_out=txt_out.replace(".txt",".bed")

	try :
		out_txt=open(txt_out,"wt")
		out_bed=open(bed_out,"wt")
		out_txt.write("Chromosome\tStart\tEnd")
		for smp in samples:
			out_txt.write("\tCov"+smp+"\tFreqC"+smp)
		smp=samples[0]
		nb_DMCs=0
		out_txt.write("\tMethyl diff\tMethylation state in "+reference_cond+"\n")
		for chr in sorted(final.keys()) :
			for start in sorted(final[chr].keys()):
				nb_DMCs+=1
				out_txt.write(chr+"\t"+str(start)+"\t"+str(start+1))
				out_bed.write(chr+"\t"+str(start)+"\t"+str(start+1)+"\n")
				for smp in samples:
					out_txt.write("\t"+str(coverages[chr+"."+str(start)][smp])+"\t"+str(occurrences_C[chr+"."+str(start)][smp]))
				out_txt.write("\t"+str(final[chr][start]))
				if final[chr][start]<0:
					out_txt.write("\thypometh")
				else:
					out_txt.write("\thypermeth")
				out_txt.write("\n")

		out_txt.close()
		out_bed.close()
	
		out_log.write("RESULT number of obvious DMCs="+str(nb_DMCs)+"\n")
		out_log.write("OUT "+txt_out+"\n")
		out_log.write("STATUS OK\n")
		out_log.close()
	except IOError as exc:
		sys.exit("Cannot create output files : {0}".format(exc))

except IOError as exc:
	sys.exit("Cannot append to log file '{0}' : {1}".format(log_file,exc))

