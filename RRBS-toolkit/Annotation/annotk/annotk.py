
import re
import sys
from sys import argv
import os
import tempfile

import time
from datetime import datetime

import warnings

from join_by_location import Join_by_location
from join_by_value import Join_by_value
from join_with_gtf import Join_with_gtf

class Annotation_theme :

	default_values={}
	#---------------------------------------
	#default values for all annotation
	default_values["keep_scaffolds"]="Yes"
	default_values["nb_max_results"]=-1 # keep all results by default
	#---------------------------------------
	#default values for gene feature annotation
	default_values["promoter_downstream"]=2000
	default_values["promoter_upstream"]=100
	default_values["tss_downstream"]=100
	default_values["tss_upstream"]=100
	default_values["tts_downstream"]=100
	default_values["tts_upstream"]=100
	default_values["feature_priorities"]="tss,promoter,tts,utr3,utr5,exon,intron"
	default_values["max_dist_nearest_gene"]=1e9
	#---------------------------------------
	#default values for others annotation
	default_values["min_overlap"]=0
	default_values["target_keys"]=[1,2,3]
	default_values["reference_keys"]=[1,2,3]
	

	def __init__(self,name) :
		self.name=name
		self.parameters={}
		self.offsets=[]

	def get_name(self) :
		return self.name

	def set_parameter(self,name,value) :
		if name == "target_keys" or name == "reference_keys" :
			#Check they are all referenced as number, then convert it into integer
			all_numbers=True
			self.parameters[name]=[]
			for key in value.split(",") :
				if re.match("^[0-9]+$",key) :
					self.parameters[name].append(int(key))
				else :
					all_numbers=False
					break;
			#Otherwise let it as it is and we will check compatibility with reference file
			#when we will read the first line
			if not all_numbers :
				self.parameters[name]=value.split(",")
		else :
			'''
			me=re.match("^(promoter|tss|tts)_offset",name)
			if me is not None :
				name=me.group(1)
				self.parameters[name+"_downstream"]=value
				self.parameters[name+"_upstream"]=value
			else :
				self.parameters[name]=value
			'''
			self.parameters[name]=value

	def get_parameter(self,name) :
		if name in self.parameters :
			return self.parameters[name]
		elif name in Annotation_theme.default_values :
			return Annotation_theme.default_values[name]
		else :
			return ""

	def add_offset(self,offset,label=None) :
		if offset not in self.offsets :
			if label is None :
				label=str(offset)
			self.offsets.append([offset,label])

	def get_offsets(self) :
		if len(self.offsets) == 0 :
			return [[0,""]]
		else :
			return sorted(self.offsets, key=lambda of: of[0])

	def check_validity(self) :
		if "reference_file" not in self.parameters :
			sys.exit("No 'reference_file' is specified for annotation theme '{0}'. Exiting.".format(self.name))
		if "join_type" not in self.parameters :
			sys.exit("No 'join_type' is specified for annotation theme '{0}'. Exiting.".format(self.name))
		if self.parameters["join_type"] == "gtf" and "reference_keys" in self.parameters :
			sys.stderr.write((\
				">>>  Warning : reference_keys specified in a 'gtf' join_type (annotation theme={0}).\n"+ \
				">>>            GTF is a fixed format. reference_keys will not be used for this join\n"
				).format(self.name)
			)

	def __str__(self) :
		return name+" annotation"

#Interpret a distance such as "1.5e3kb"
distance_regexpr="([0-9]+([.][0-9]+)?([Ee][+]?[0-9]+)?)([A-Za-z]{2})?"

def get_distance_value(parameter,me,value_group=1,unit_group=4) :
	global no_line, file_config
	try :
		value=float(me.group(value_group))
	except ValueError :
		sys.exit(
			(
			"Cannot convert to float value '{0}' specified for '{1}' parameter on line #{2} "+
			"of configuration file '{3}'."
			).format(me.group(1),parameter,no_line,file_config)
		)
		
	unit=me.group(unit_group)
	if unit is not None :
		unit=unit.lower()
		if unit == "bp" :
			pass
		elif unit == "kb" :
			value*=1000
		elif unit == "mb" :
			value*=1e6
		else :
			sys.exit(
				(
				"Unexpected unit '{0}' specified for '{1}' parameter on line #{2} "+
				"of configuration file '{3}'. Expected 'bp', 'kb' or 'mb'"
				).format(unit,parameter,no_line,file_config)
			)
	else :
		unit=""
	if value > 1e9 : #Not accepted for an integer
		value=1e9
	value=int(value)
	return value

###############################################################################
# Start of main program
###############################################################################
file_config=argv[1]

try :
	in_config=open(file_config,"rt")
except IOError as exc:
	sys.exit("Cannot open input file '{0}' : {1}".format(file_config,exc))

global_start_time=datetime.fromtimestamp(time.time())
try :
	in_theme=False
	theme=None
	themes=[]
	no_line=0
	keep_scaffolds=""
	file_format="tab"
	for line in in_config.readlines() :
		no_line+=1
		line=line.rstrip("\r\n")
		me=re.match("^[\t ]*$",line)
		if me :
			continue
		me=re.match("^[ \t]*#.*$",line)
		if me :
			continue
		me=re.match("^file_to_annotate[\t ]+([^#\t]+).*$",line)
		if me :
			file_to_annotate=me.group(1)
			continue
		me=re.match("^file_format[\t ]+([^#\t]+).*$",line)
		if me :
			file_format=me.group(1)
			if file_format not in ('tab','fasta') :
				sys.exit(
				"'file_format' parameter specified on line #{0} of configuration file '{1}' should be equal to 'tab' or 'fasta'.".format(
					no_line,file_config)
				)
			continue
		me=re.match("^output_file[\t ]+([^#\t]+).*$",line)
		if me :
			file_out=me.group(1)
			continue
		me=re.match("^keep_scaffolds[\t ]+([^# \t]+).*$",line)
		if me :
			keep_scaffolds=me.group(1).lower()
			continue
		me=re.match("^theme[\t ]+([^#\t]+).*$",line)
		if me :
			if theme is not None :
				#Validate previous theme
				theme.check_validity()
			theme=Annotation_theme(me.group(1))
			if file_format != "" :
				theme.set_parameter("file_format",file_format)
				
			if keep_scaffolds != "" :
				theme.set_parameter("keep_scaffolds",keep_scaffolds)
			themes.append(theme)
			in_theme=True
			continue
		#Theme properties
		me=re.match("^[\t ]*join_type[\t ]+([^# \t]+).*$",line)
		if me :
			if not in_theme :
				sys.exit(
				"'join_type' parameter specified on line #{0} of configuration file '{1}' should be placed in a theme section.".format(
					no_line,file_config)
				)
			value=me.group(1)
			if value not in [ "value","location","gtf"] :
				sys.exit(
				"'join_type' parameter specified on line #{0} of configuration file '{1}' should be equal to 'gtf', 'value' or 'location'.".format(
					no_line,file_config)
				)
				
			theme.set_parameter('join_type',value)
			continue
		me=re.match("^[\t ]*reference_file[\t ]+([^#\t]+).*$",line)
		if me :
			if not in_theme :
				sys.exit(
				"'reference_file' parameter specified on line #{0} of configuration file '{1}' should be placed in a theme section.".format(
					no_line,file_config)
				)
			theme.set_parameter('reference_file',me.group(1))
			continue
		me=re.match("^[\t ]*min_overlap[\t ]+([0-9]+)%?.*$",line)
		if me :
			if not in_theme :
				sys.exit(
				"'min_overlap' parameter specified on line #{0} of configuration file '{1}' should be placed in a theme section.".format(
					no_line,file_config)
				)
			min_overlap=int(me.group(1))
			if min_overlap>100 or min_overlap<0 :
				sys.exit("'min_overlap' parameter shoud be specified as a %. It cannot be greater than 100 or lower than 0.")

			theme.set_parameter('min_overlap',min_overlap)
			continue
		me=re.match("^[\t ]*interval_shift[\t ]+"+distance_regexpr+"([ \t]+([^#\t]+))?.*$",line)
		if me :
			if not in_theme :
				sys.exit(
				"'interval_shift' parameter specified on line #{0} of configuration file '{1}' should be placed in a theme section.".format(
					no_line,file_config)
				)
			distance=get_distance_value("interval_shift",me)
			theme.add_offset(distance,me.group(6))
			continue
		#me=re.match("^[\t ]*(tss|tts|promoter)_(offset|upstream|downstream)[\t ]+"+distance_regexpr+"([ \t].*)?$",line)
		me=re.match("^[\t ]*(tss|tts|promoter)_(upstream|downstream)[\t ]+"+distance_regexpr+"([ \t].*)?$",line)
		if me :
			feature_name=me.group(1)+"_"+me.group(2)
			if not in_theme :
				sys.exit(
				"'{0}' parameter specified on line #{1} of configuration file '{2}' should be placed in a theme section.".format(
					feature_name,no_line,file_config)
				)
			distance=get_distance_value(feature_name,me,value_group=3,unit_group=6)
			theme.set_parameter(feature_name,distance)
			continue
		me=re.match("^[\t ]*feature_priorities[\t ]+([^#\t]+).*$",line)
		if me :
			if not in_theme :
				sys.exit(
				"'feature_priorities' parameter specified on line #{0} of configuration file '{1}' should be placed in a theme section.".format(
					no_line,file_config)
				)
			theme.set_parameter('feature_priorities',me.group(1))
			continue
		me=re.match("^[\t ]*max_dist_nearest_gene[\t ]+"+distance_regexpr+"([ \t].*)?$",line)
		if me :
			if not in_theme :
				sys.exit(
				"'max_dist_nearest_gene' parameter specified on line #{0} of configuration file '{1}' should be placed in a theme section.".format(
					no_line,file_config)
				)
			max_dist_nearest_gene=get_distance_value("max_dist_nearest_gene",me)
			theme.set_parameter("max_dist_nearest_gene",max_dist_nearest_gene)
			continue
		me=re.match("^[\t ]*nb_max_results[\t ]+([0-9]+|[Aa][Ll][Ll]).*$",line)
		if me :
			if not in_theme :
				sys.exit(
				"'nb_max_results' parameter specified on line #{0} of configuration file '{1}' should be placed in a theme section.".format(
					no_line,file_config)
				)
			if me.group(1)=="0" :
				sys.exit(("Invalid value for 'nb_max_results' parameter on line #{0} of configuration file '{1}'."+
					  " Found '0'. Expected either a positive non null integer or 'All'.").format(no_line,file_config))
			if me.group(1).lower()=="all" :
				theme.set_parameter('nb_max_results',-1)
			else :
				theme.set_parameter('nb_max_results',int(me.group(1)))
			continue
		me=re.match("^[\t ]*(target|reference)_keys[\t ]+([^#\t]+).*$",line)
		if me :
			if not in_theme :
				sys.exit(
				"'{0}_keys' parameter specified on line #{1} of configuration file '{2}' should be placed in a theme section.".format(
					me.group(1),no_line,file_config)
				)
			keys=re.sub(", *",",",me.group(2))
			theme.set_parameter(me.group(1)+"_keys",keys)
			continue
		#Error
		sys.exit("Cannot interpret line #{0} of configuration file '{1}' :\n{2}".format(no_line,file_config,line))

	#Validate last theme
	if theme is not None :
		theme.check_validity()
	else :
		sys.exit("No annotation theme has been specified in configuration file '{0}'. Exiting.".format(file_config))
		
except IOError as exc:
	sys.exit("Cannot read input file '{0}' : {1}".format(file_config,exc))

in_config.close()

################ End of config file parsing #######################

def get_duration(start_time) :
	end_time=datetime.fromtimestamp(time.time())
	elapsed=end_time-start_time
	return str(elapsed).split(".")[0]

file_in=file_to_annotate
if file_format == "fasta" :
	print "----------------------------------------------------"
	print "Converting fasta to tab format ..."
	start_time=datetime.fromtimestamp(time.time())
	#Convert fasta to tab
	fh_tmp=tempfile.NamedTemporaryFile()
	file_tmp=fh_tmp.name
	fh_tmp.close()

	try :
		in_file=open(file_in)
	except IOError as exc:
		sys.exit("Cannot read file to annotate '{0}' : {1}".format(file_in,exc))

	#get file size
	file_size=os.stat(file_in).st_size

	try :
		out_file=open(file_tmp,"wt")
	except IOError as exc:
		sys.exit("Cannot create temporary output file '{0}' : {1}".format(file_tmp,exc))

	try :
		no_line=no_header=0
		current_position=0
		for line in in_file.readlines() :

			no_line+=1
			current_position+=len(line)

			if no_line % 1e5 ==0 :
				sys.stdout.write("\t{0} lines read from reference ... ({1}% completed)\r".format(no_line,100*current_position/file_size))
				sys.stdout.flush()

			me=re.match("^>([^ \t]+)_([0-9]+)_([0-9]+).*$",line)
			if me is None :
				me=re.match("^>([^ \t]+)_([0-9]+).*$",line)
				if me is None :
					continue
				elif no_line==1 :
					out_file.write("Chromosome\tPosition\n")
					genomic_type="positions"
				line="{0}\t{1}".format(me.group(1),me.group(2))
				for theme in themes :
					if theme.get_parameter("join_type") != "value" :
						theme.set_parameter("target_keys","1,2")
			else :
				for theme in themes :
					if theme.get_parameter("join_type") != "value" :
						theme.set_parameter("target_keys","1,2,3")
				if no_line==1 :
					out_file.write("Chromosome\tStart\tEnd\n")
					genomic_type="regions"
				line="{0}\t{1}\t{2}".format(me.group(1),me.group(2),me.group(3))
			
			out_file.write("{0}\n".format(line))
			no_header+=1

		in_file.close()
		out_file.close()
		file_in=file_tmp
	except IOError as exc:
		sys.exit("An I/O error occurred while trying to convert FASTA to BED format : {0}".format(exc))
	print "\nConversion done ! {0} genomic {1} extracted. (duration: {2})".format(no_header,genomic_type,get_duration(start_time))

#Run annotations
for i in range(0,len(themes)) :
	if i != len(themes) - 1 :
		#Not the last annotation
		fh_tmp=tempfile.NamedTemporaryFile()
		file_tmp=fh_tmp.name
		fh_tmp.close()
	else :
		file_tmp=file_out

	theme=themes[i]

	join_type=theme.get_parameter("join_type")
	theme_name=theme.get_name()

	print "----------------------------------------------------"
	print "{0} annotation :".format(theme_name)
	start_time=datetime.fromtimestamp(time.time())

	if join_type == "location" :
		join=Join_by_location(theme)
		join.run_annotation(file_in,file_tmp)
	elif join_type == "value" :
		join=Join_by_value(theme)
		join.run_annotation(file_in,file_tmp)
	elif join_type == "gtf" :
		join=Join_with_gtf(theme)
		join.run_annotation(file_in,file_tmp)
	else :
		sys.exit("Unsupported 'join_type' : {0} in annotation theme '{1}'. Exiting.".format(join_type,theme_name))

	#clean up join used
	del join

	file_in=file_tmp
	print "Annotation of {0} done ! (duration: {1})".format(theme_name,get_duration(start_time))
print "----------------------------------------------------"
print "Annotation of {0} completed ! (duration: {1})".format(file_to_annotate,get_duration(global_start_time))
