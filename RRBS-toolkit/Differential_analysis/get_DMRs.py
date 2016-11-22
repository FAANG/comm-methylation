import os
import re
import sys
from sys import argv


###################
debug=0;
###################

config_file=argv[1];
log_file=argv[2];

file_in=""
from_merge_step=False;

if os.path.isfile(log_file) :
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
	
	if "merge_DMCs.py" in step2file:
		file_in=step2file["merge_DMCs.py"];
		from_merge_step=True;
		txt_out=file_in.replace("with obvious DMCs.txt","DMRs.txt")
	else :
		file_in=step2file["get_obvious_DMC.py"];
		if file_in != "":
			txt_out=file_in.replace("obvious_DMCs","obvious_DMRs")
		else :
			sys.exit("Neither a DMC file obtained by merge or get obvious DMCs reported in log file : $logFile.")

#####################
## Default values
#####################
min_nb_DMCs=3;
max_distance_between_DMCs=100;
stat_value="pvalue";
stat_threshold1=0.01;
stat_threshold2=0.05;
output_dir=".";
only_DMR=False

###############
# Read config
###############
try :
	in_config=open(config_file,"rt")
	state=0
	samples=[]
	sample2cond={}
	reference_cond=""
	for line in in_config.readlines():
		line=line.rstrip("\n")
		me=re.match("^#nb_min_DMCs_in_DMRs\t([^#]*)(#.*)?$",line)
		if me is not None:
			min_nb_DMCs=int(me.group(1))
			continue
		me=re.match("^#max_distance_between_DMCs\t([^#]*)(#.*)?$",line)
		if me is not None:
			max_distance_between_DMCs=int(me.group(1))
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
		me=re.match("^#DMC_file\t([^#]*)(#.*)?$",line)
		if me is not None:
			file_in=me.group(1)
			only_DMR=True
			continue
		me=re.match("^#DMR_file\t([^#]*)(#.*)?$",line)
		if me is not None:
			txt_out=me.group(1)
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
		if reference_cond == "" :
			reference_cond=cond
		sample2cond[smp]=cond
		samples.append(smp)
	in_config.close()
except IOError as exc:
	sys.exit("Cannot open config file '{0}' : {1}".format(config_file,exc))

if only_DMR:
	if txt_out == "" :
		sys.exit("User asked only for a DMR detection from '"+file_in+"' but no output file has been specified using DMC_file parameter")
	if os.path.basename(txt_out) == txt_out :
		txt_out=output_dir+"/"+txt_out

if file_in == "" :
	sys.exit("Do not know from which file containong DMC we should infer DMRs. Exiting.")


try:
	out_log=open(log_file,"at")
	out_log.write("CMD get_DMRs.py\n")
	out_log.write("\tConfiguration file :\n")
	out_log.write("\t--------------------\n")
	out_log.write("\t\tmin_DMCs="+str(min_nb_DMCs)+"\n")
	out_log.write("\t\tmax_distance="+str(max_distance_between_DMCs)+"\n")

	if from_merge_step:
		out_log.write("\t\tstat_value="+stat_value+"\n")
		out_log.write("\t\tstat_threshold1="+str(stat_threshold1)+"\n")

	if not only_DMR:
		out_log.write("\t\tstat_threshold2="+str(stat_threshold2)+"\n")

	out_log.write("\t\toutput_dir="+output_dir+"\n")
	out_log.close()
except IOError as exc:
	sys.exit("Cannot append to log file '{0}' : {1}".format(log_file,exc))

#####################
# read list of DMCs
#####################
try:
	DMCs={}
	in_file=open(file_in,"rt")
	no_line=0
	for line in in_file.readlines():
		no_line+=1
		if no_line==1:
			continue
		line=line.rstrip("\n")
		elmts=line.split("\t")
		chr=elmts[0]
		start=int(elmts[1])
		fc=elmts[-1]
		if chr not in DMCs:
			DMCs[chr]={}
		DMCs[chr][start]=fc
	in_file.close()
except IOError as exc:
	sys.exit("Cannot read input file '{0}' : {1}".format(file_in,exc))

#####################
# identify DMRs
#####################
def new_DMR() :
	global nb_DMRs, nb_hypo, nb_hyper
	if debug :
		print "DMR ["+str(island_start)+";"+str(last_start)+"] :"+",".join(list_DMCs)
	out_txt.write(	chr+"\t"+str(island_start)+"\t"+str(last_start)+"\t"+ \
			str(last_start-island_start)+"\t"+last_fc+"\t" + \
			",".join(list_DMCs)+"\t"+str(len(list_DMCs))+"\n"
	)
	if last_fc == "hypometh":
		nb_hypo+=1
		id_DMR="hypo_"+str(nb_hypo)
		score=-1
	else :
		nb_hyper+=1
		id_DMR="hyper_"+str(nb_hyper)
		score=1

	out_bed.write(	chr+"\t"+str(island_start)+"\t"+str(last_start)+"\t"+id_DMR+"\t"+str(score)+"\n")
	if chr not in composition_of_DMRs:
		composition_of_DMRs[chr]={}
		DMRs[chr]={}
	composition_of_DMRs[chr][island_start]=list_DMCs
	DMRs[chr][island_start]=str(last_start)+"\t"+last_fc
	nb_DMRs+=1

try :
	nb_DMRs=nb_hypo=nb_hyper=0
	composition_of_DMRs={}
	DMRs={}
	out_txt=open(txt_out,"wt")
	bed_out=txt_out.replace(".txt",".bed")
	out_bed=open(bed_out,"wt")

	if reference_cond != "" :
		out_txt.write("Chromosome\tDMR start\tDMR end\tDMR length\tMethylation state for "+reference_cond+"\tList of DMCs\tNumber of DMCs\n")
	else:
		out_txt.write("Chromosome\tDMR start\tDMR end\tDMR length\tMethylation state\tList of DMCs\tNumber of DMCs\n")

	for chr in sorted(DMCs.keys()) :
		island_start=-1
		last_fc=""
		last_start=0
		nb_DMCs=0
		for start in sorted(DMCs[chr].keys()):
			fc=DMCs[chr][start]

			'''
			if start>=5253420 and start<=5255368 :
				debug=1
			else:
				debug=0
			'''
			if debug:
				print "--------"
				print "start="+str(start)+"/fc="+fc+"/last_fc="+last_fc+"/dist_previous="+str(start-last_start)
				print "\tisland_start="+str(island_start)+"/nb_DMCs="+str(nb_DMCs)
			if island_start==-1 :
				#Start a new candidate for island
				island_start=start
				list_DMCs=[str(island_start)]
				nb_DMCs=1
			else :
				if (start-last_start)>max_distance_between_DMCs or last_fc != fc :
					if debug :
						if last_fc != fc :
							print "Stop candidate DMR because of fc."
						else :
							print "Stop candidate DMR because of distance : start-last_start="+str(start)+"-"+str(last_start)+"="+ \
								str(start-last_start)+">"+str(max_distance_between_DMCs)
							
					#End of previous candidate DMR
					if nb_DMCs>=min_nb_DMCs :
						#This is a DMR
						new_DMR()

					island_start=start
					list_DMCs=[str(island_start)]
					nb_DMCs=1
				else:
					list_DMCs.append(str(start))
					nb_DMCs+=1
			last_fc=fc
			last_start=start
		if nb_DMCs>=min_nb_DMCs :
			new_DMR()

	out_txt.close()
	out_bed.close()
except IOError as exc:
	sys.exit("Cannot create output file '{0}' : {1}".format(txt_out,exc))

try:
	out_log=open(log_file,"at")
	out_log.write("RESULT Number of DMRs identified="+str(nb_DMRs)+"\n")
	out_log.close()
except IOError as exc:
	sys.exit("Cannot append to log file '{0}' : {1}".format(log_file,exc))


#####################
# Extend DMRs
#####################
if from_merge_step :
	#Try to extend DMRs with DMCs which have a pvalue <stat2Threshold
	file_stat=step2file["get_diff_methyl.R"];
	txt_out=txt_out.replace("DMRs.txt","DMRs extended.txt")
	txt_out=txt_out.replace(stat_value+str(stat_threshold1),stat_value+str(stat_threshold2))
	bed_out=txt_out.replace(".txt",".bed")

	stat_DMCs={}
	try :
		in_stat=open(file_stat,"rt")
		no_line=0
		for line in in_stat.readlines():
			no_line+=1
			if no_line == 1 :
				continue
			line=line.rstrip("\n")
			elmts=line.split("\t")
			chr=elmts[0]
			start=int(elmts[1])
			pv=float(elmts[-3])
			if pv<stat_threshold1 :
				continue
			if pv>=stat_threshold2 :
				continue
			
			fc=elmts[-1]
			if chr not in stat_DMCs:
				stat_DMCs[chr]={}
			stat_DMCs[chr][start]=fc

		in_stat.close()
	except IOError as exc:
		sys.exit("Cannot read file resulting from statistical analysis '{0}' : {1}".format(stat_file,exc))

	new_DMRs={}
	for chr in DMRs :
		DMCs=sorted(stat_DMCs[chr].keys())
		extended_DMRs={}
		for island_start in sorted(DMRs[chr]) :
			(island_end,fc_DMR)=DMRs[chr][island_start].split("\t")
			island_end=int(island_end)
			new_start=island_start
			new_end=island_end
			if debug :
				print "Treating DMR ["+str(island_start)+";"+str(island_end)+"] ("+fc_DMR+")"
			#Try to extend DMR on the right
			for idx in range(0,len(DMCs)):
				if DMCs[idx]>island_end :
					break
			extended_right=False
			while idx<len(DMCs) and DMCs[idx]>island_end and DMCs[idx]-island_end<max_distance_between_DMCs and stat_DMCs[chr][DMCs[idx]] == fc_DMR :
				extended_right=True
				if debug :
					print "\tDMR["+str(island_start)+";"+str(island_end)+"] extended on the right to "+str(DMCs[idx])+" (dist="+str(DMCs[idx]-island_end)+")"
				composition_of_DMRs[chr][island_start].append(str(DMCs[idx]))
				idx+=1
			if extended_right:
				new_end=DMCs[idx-1]

			#Try to extend DMR on the left
			for idx in range(len(DMCs)-1,-1,-1):
				if DMCs[idx]<island_start :
					break
			extended_left=False
			while idx>=0 and DMCs[idx]<island_start and island_start-DMCs[idx]<max_distance_between_DMCs and stat_DMCs[chr][DMCs[idx]] == fc_DMR :
				extended_left=True
				if debug :
					print "\tDMR["+str(island_start)+";"+str(island_end)+"] extended on the left to "+str(DMCs[idx])+" (dit="+str(island_start-DMCs[idx])+")"
				composition_of_DMRs[chr][island_start].insert(0,str(DMCs[idx]))
				idx-=1
			if extended_left:
				new_start=DMCs[idx+1]

			if extended_left or extended_right :
				if debug:
					print "DMRs["+str(island_start)+";"+str(island_end)+"] extended to ["+str(new_start)+";"+str(new_end)+"] ("+fc_DMR+")"
				composition_of_DMRs[chr][new_start]=composition_of_DMRs[chr][island_start]
			elif debug :
				print "DMRs["+str(island_start)+";"+str(island_end)+"] unchanged ("+fc_DMR+")"

			extended_DMRs[new_start]=str(new_end)+"\t"+fc_DMR
		#Find overlapping DMRs
		if debug :
			print "----"
		while True:
			has_changed=False
			new_extended=dict()
			starts=sorted(extended_DMRs)
			skip_next=False
			for idx in range(0,len(starts)-1) :
				if skip_next :
					skip_next=False
					continue
				skip_next=False
				island_start=starts[idx]
				(island_end,fc_DMR)=extended_DMRs[island_start].split("\t")
				island_end=int(island_end)

				next_start=starts[idx+1]
				(next_end,next_fc)=extended_DMRs[next_start].split("\t")

				if next_start-island_end<max_distance_between_DMCs and fc_DMR == next_fc:
					if debug :
						print "Joining ["+str(island_start)+";"+str(island_end)+"] and ["+str(next_start)+";"+str(next_end)+"]"
					new_extended[island_start]=str(next_end)+"\t"+fc_DMR
					composition_of_DMRs[chr][island_start].extend(composition_of_DMRs[chr][next_start])
					has_changed=True
					skip_next=True
				else :
					new_extended[island_start]=str(island_end)+"\t"+fc_DMR
			if not skip_next :
				idx=len(starts)-1
				island_start=starts[idx]
				new_extended[island_start]=extended_DMRs[island_start]
			
			if not has_changed:
				break
			extended_DMRs=new_extended
		new_DMRs[chr]={}

		for start in extended_DMRs :
			new_DMRs[chr][start]=extended_DMRs[start]
			composition_of_DMRs[chr][island_start]=set(composition_of_DMRs[chr][island_start])
	#Output
	try :
		out_txt=open(txt_out,"wt")
		out_bed=open(bed_out,"wt")
		nb_hypo=nb_hyper=0
		nb_DMRs=0
		out_txt.write("Chromosome\tDMR start\tDMR end\tDMR length\tMethylation state for "+reference_cond+"\tList of DMCs\tNumber of DMCs\n")
		for chr in new_DMRs :
			for island_start in sorted(new_DMRs[chr]) :
				nb_DMRs+=1
				(island_end,fc_DMR)=new_DMRs[chr][island_start].split("\t")
				island_end=int(island_end)

				#Unify and sort list of CpGs
				list_DMCs=list(sorted(set(composition_of_DMRs[chr][island_start])))
				out_txt.write(	chr+"\t"+str(island_start)+"\t"+str(island_end)+"\t"+ \
						str(island_end-island_start)+"\t"+fc_DMR+"\t" + \
						",".join(list_DMCs)+"\t"+str(len(list_DMCs))+"\n"
				)
				if fc_DMR == "hypometh":
					nb_hypo+=1
					id_DMR="hypo_"+str(nb_hypo)
					score=-1
				else :
					nb_hyper+=1
					id_DMR="hyper_"+str(nb_hyper)
					score=1

				out_bed.write(	chr+"\t"+str(island_start)+"\t"+str(last_start)+"\t"+id_DMR+"\t"+str(score)+"\n")
			
		out_txt.close()
		out_bed.close()	
	except IOError as exc:
		sys.exit("Cannot create output file for extended DMRs '{0}' : {1}".format(txt_out,exc))
try:
	out_log=open(log_file,"at")
	out_log.write("RESULT Number of extended DMRs identified="+str(nb_DMRs)+"\n")
	out_log.write("STATUS OK")
	out_log.close()
except IOError as exc:
	sys.exit("Cannot append to log file '{0}' : {1}".format(log_file,exc))
