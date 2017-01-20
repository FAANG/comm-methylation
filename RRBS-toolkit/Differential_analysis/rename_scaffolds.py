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

import os
import re
import glob
import sys
from sys import argv

step=int(argv[1]);
config_file=argv[2];
log_file=argv[3];
tmp_dir=argv[4];
pid=argv[5];

if not os.path.isfile(config_file) :
	sys.exit("Unable to find configuration file for rename_scaffolds : '"+config_file+"'")

files=[]
try :
	with open(config_file,"rt") as in_config:
		state=0
		for line in in_config.readlines():
			line=line.rstrip('\n')
			if re.match("^ *$",line) :
				continue
			mre=re.match("#stat_method[ \t]*(methylKit|methylSig).*$",line)
			if mre is not None:
				statistical_method=mre.group(1)
			if re.match("^Sample",line) :
				state=1
				continue
			if state == 0 :
				continue
			elmts=line.split("\t")
			files.append(elmts[1])

except IOError as exc:
	sys.exit("Cannot open configuration file for rename_scaffolds '{0}' : {1}".format(config_file,exc))

chromosome_table={}
if step == 1:
	try :
		with open(log_file,"at") as out_log:
			out_log.write("CMD rename_scaffolds.py\n")
			out_log.write("FLAVOR renaming scaffolds in chromosome number\n")
	
			try :
				tab1_file=tmp_dir+"/chromosome_table."+pid+".txt"
				out_file1=open(tab1_file,"wt")
				out_file1.write("Scaffold\tChromosome number\n")

				tab2_file=tmp_dir+"/sample2file_table."+pid+".txt"
				out_file2=open(tab2_file,"wt")
				out_file2.write("Original file\tActual file\n")

				no_chr=100
				no_file=0
				for file_in in files:
					no_file+=1
					out_log.write("\tTreating "+file_in+" ...\n")
					try :
						with open(file_in,"rt") as in_file:
							file_out=tmp_dir+"/"+os.path.basename(file_in)+"."+pid+"."+str(no_file);
							out_file2.write(file_in+"\t"+file_out+"\n")
							try :
								out_file=open(file_out,"wt")
								no_line=0
								for line in in_file.readlines():
									line=line.rstrip("\n")
									no_line+=1
									if no_line == 1:
										#if statistical_method == "methylKit":
										line="chrBase	chr	base	Strand	coverage	freq_C	freq_T"
										out_file.write(line+"\n")
										continue
									elmts=line.split("\t")
									chr=elmts[0]
									if chr not in chromosome_table:
										no_chr+=1
										chromosome_table[chr]=no_chr
										out_file1.write(chr+"\t"+str(no_chr)+"\n")
									elmts[0]=str(chromosome_table[chr])
									#if statistical_method == "methylKit":
									line=elmts[0]+"."+elmts[1]+"\t"+elmts[0]+"\t"+elmts[1]+"\tF\t"+elmts[2]
									freq_C=float(elmts[3])/float(elmts[2])*100.0
									freq_T=100.0-freq_C
									line=line+"\t"+str(freq_C)+"\t"+str(freq_T)
									#else:
									#	line="\t".join(elmts)
									out_file.write(line+"\n")
								out_file.close()
							except IOError as exc:
								sys.exit("Unable to create alias file '{0}' : {1}".format(file_out,exc))
							#End of loop on each line of input file
						#End of with open on input file
					#End of try on create file
					except IOError as exc:
						sys.exit("Unable to open input file '{0}' : {1}".format(file_in,exc))
				out_file1.close()
				out_file2.close()
				#End of loop on each input file
			#End of try on create chromosome and sample2table files
			except IOError as exc:
				sys.exit("Unable to create chromosome table file : {0}".format(exc))
			out_log.write("STATUS OK\n")
		#End of with open log_file
	#End of try
	except IOError as exc:
		sys.exit("Unable to open log file '"+log_file+" : {0}".format(exc))
else:
	file_to_treat="";
	try :
		with open(log_file,"rt") as in_log:
			for line in in_log.readlines():
				line=line.rstrip("\n")
				me=re.match("^CMD (.*)$",line)
				if me is not None:
					step=me.group(1)
					continue

				me=re.match("^OUT (.*)$",line)
				if me is not None:
					file_to_treat=me.group(1)
					if step == "get_diff_methyl.R":
						break

	except IOError as exc:
		sys.exit("Unable to open log file '"+log_file+" : {0}".format(exc))

	chr_table_file=tmp_dir+"/chromosome_table."+pid+".txt"
	try:
		out_log=open(log_file,"at")
		out_log.write("CMD rename_scaffolds.py\n")
		out_log.write("FLAVOR renaming chromosome number with scaffolds\n")
		if file_to_treat == "":
			out_log.write("ERROR Cannot find output file of R treatment\n")
			out_log.write("STATUS KO\n")
			out_log.close()
			sys.exit("Cannot find output file of R treatment")
		
		if not os.path.isfile(chr_table_file):
			out_log.write( "ERROR Cannot find chromosome table file\n")
			out_log.write( "STATUS KO\n")
			close(LOG);
			sys.exit("Cannot find chromosome table file")

		try:
			in_chr_table=open(chr_table_file,"rt")
			no_line=0
			for line in in_chr_table.readlines():
				no_line+=1
				if no_line==1:
					continue
				line=line.rstrip("\n")
				elmts=line.split("\t")
				chr=elmts[0]
				no_chr=elmts[1]
				chromosome_table[no_chr]=chr
			in_chr_table.close()
		except IOError as exc:
			sys.exit("Unable to read chromosome table file '"+chr_table_file+" : {0}".format(exc))
	
		file_to_treat=re.sub("[pq]value[.0-9]+.txt","*.txt",file_to_treat)

		files_to_treat=glob.glob(file_to_treat)
		for file_to_treat in files_to_treat :
			file_out=file_to_treat.replace(".txt",".tmp")
			try :
				in_file=open(file_to_treat,"rt")
				out_file=open(file_out,"wt")
				no_line=0
				for line in in_file.readlines():
					line=line.rstrip("\n")
					no_line+=1
					if no_line==1:
						out_file.write(line+"\n")
						continue
					elmts=line.split("\t")
					no_chr=elmts[0]
					pos=elmts[1]
	
					if no_chr in chromosome_table:
						elmts[0]=chromosome_table[no_chr]
					line="\t".join(elmts);
					out_file.write(line+"\n")
				in_file.close()
				out_file.close()
				os.rename(file_out,file_to_treat)
			except IOError as exc:
				sys.exit("Unable to replace chromosome value in file '"+chr_table_file+" : {0}".format(exc))
		out_log.write("STATUS OK\n")
	except IOError as exc:
		sys.exit("Unable to write to log file '"+log_file+" : {0}".format(exc))


