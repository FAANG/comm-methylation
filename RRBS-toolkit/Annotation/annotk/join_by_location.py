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
import sys
from sys import argv
import re
from bx.intervals.intersection import IntervalTree,Interval

"""
	the boundaries are not contained in the interval with bx module.
	example :

	ivt.insert_interval( Interval(10,20) )
	ivt.insert_interval( Interval(20,30) )
	print "result={0}".format(ivt.find(20,20))
	result=[]

	therefore, when we use find method, we always transform the target boundaries :
		start boundary -1 
		end boundary +1 

	such as :
		interval_tree.find(target_start-1,target_end+1))
"""

class Join_by_location :

	debug=False

	def __init__(self,theme) :
		self.theme=theme

	def verify_key_columns(self,file,header_elmts,keys) :
		if type(keys[0]).__name__=="str" :
			#Target keys are specified as column name : replace names with corresponding column numbers
			for i in range(0,len(header_elmts)) :
				for j in range(0,len(keys)) :
					if keys[j] == header_elmts[i] :
						keys[j] = i+1
	
			#Verify all joining columns name has been found
			for j in range(0,len(keys)) :
				if type(keys[j]).__name__ == "str" :
					#Column name not found
					sys.exit(("Could not find joining column '{0}' "+ \
						  "in first line of file '{1}'. Exiting.").format(keys[j],file))
	
	def log_already_completed(self,message,file_size,position) :
		achieved=100*position/file_size
		sys.stdout.write("\t{0} ... ({1}% completed)\r".format(
			message,achieved
		))
		sys.stdout.flush()

	def read_reference(self,file_ref,reference_keys,offsets=[[0,""]]):
	
		#if len(reference_keys)==2 :
		#	sys.exit("Only 2 columns provided to indicate joining key for reference file '{0}'. Exiting.".format(file_ref))
	
		print "Read reference ..."
	        regions = {}
	        annotations = {}
	
	        in_reference = open(file_ref)
		file_size=os.stat(file_ref).st_size
		current_position=0
	
		no_line = 0
	        for line_region in in_reference:

			current_position+=len(line_region)
			no_line = no_line + 1

			#if (no_line< 1e5 and no_line % 1000 == 0) or (no_line<1e6 and no_line % 1e4 ==0) or (no_line>1e6 and no_line % 1e5 ==0) :
			if no_line % 1e5 ==0 :
				self.log_already_completed("{0} lines read from reference".format(no_line),file_size,current_position)
	
	                line_region = line_region.rstrip('\r\n')
	
	                elmts = line_region.split('\t')
	
	                if no_line == 1:
				header=""
				self.verify_key_columns(file_ref,elmts,reference_keys)
				skip={}
				for i in range(0,len(elmts)):
					#part of reference_keys ?
					skip[i]=False
					for j in range(0,len(reference_keys)) :
						if i+1 == reference_keys[j] :
							skip[i]=True
							break
					if skip[i] :
						continue
					if header != "" :
						header+="\t"
					header+=elmts[i]
					nb_fields = len(elmts)
	                        continue
	
			#Verify # of fields is the same as in header
			if len(elmts) != nb_fields:
				sys.exit("Line #"+str(no_line)+"' in '"+file_ref+"' contains "+str(len(elmts))+" fields "+
					 "while header line contains "+str(nb_fields)+" fields. Exiting."
				)
	
			if len(reference_keys) ==1 :
				#Region should be specified as chr:start-end
				me=re.match("^(.*):([0-9]+)-([0-9]+)$",elmts[reference_keys[0]-1])
				if me is None :
					me=re.match("^(.*):([0-9]+)$",elmts[reference_keys[0]-1])
					if me is None :
						sys.exit("Could not interpret localisation '{0}' on line #{1} of reference file {2}. Exiting.".format( \
							elmts[reference_keys[0]-1],no_line,file_in) \
						)
					chr_region=me.group(1)
					start_region=int(me.group(2))
					end_region=start_region
				else :
					chr_region=me.group(1)
					start_region=int(me.group(2))
					end_region=int(me.group(3))
			elif len(reference_keys) >=2 :
		        	chr_region = elmts[reference_keys[0]-1]
		
		                start_region = int(elmts[reference_keys[1]-1])
				end_region = start_region + 1

			if len(reference_keys) == 3 :
		                end_region = int(elmts[reference_keys[2]-1])
	
			chr_region = chr_region.lower().replace("chr","")

			if Join_by_location.debug and chr_region != "1":
				break
		
			if end_region < start_region:
				sys.exit("End of region before start of region in '{0}' on line #{1}.".format(file_ref,no_line))

	                if not chr_region in annotations:
	                        annotations[chr_region] = {}
	
			#Keep extra informations
			annotations[chr_region][start_region]=""
			for i in range(0,len(elmts)):
				if skip[i] :
					continue
				if annotations[chr_region][start_region] != "" :
					annotations[chr_region][start_region]+="\t"
				annotations[chr_region][start_region]+=elmts[i]
	
			#Reference region
			for offset in offsets:
				(offset,offset_label)=offset
	                	if not offset in regions:
	                        	regions[offset] = {}
	                	if not chr_region in regions[offset]:
	                        	regions[offset][chr_region] = IntervalTree()
	
				start=start_region-offset
				if start<=0:
					start=0

				end=end_region+offset

		                regions[offset][chr_region].insert_interval( Interval(start,end,value=(start_region,end_region)))
	
	
	        in_reference.close()
		print "\n\t{0} lines read from reference in total.".format(no_line)
	        return header, regions, annotations
	
	def run_annotation(self,file_in,file_out) :

		theme=self.theme.get_name()
		file_ref=self.theme.get_parameter("reference_file")
		target_keys=self.theme.get_parameter("target_keys")
		reference_keys=self.theme.get_parameter("reference_keys")
		minimal_overlap=self.theme.get_parameter("min_overlap")
		offsets=self.theme.get_offsets()

		keep_scaffolds=self.theme.get_parameter("keep_scaffolds").lower()
		if keep_scaffolds[0] != "n" :
			keep_scaffolds=True
		else :
			keep_scaffolds=False

		#Read input file
		target_is_region=False
		if len(target_keys)!=2 :
			target_is_region=True

		nb_max_results=self.theme.get_parameter("nb_max_results")
		
		no_scaffolds_filtered=0
		
		try:
			try:
				in_file=open(file_in,"rt")
			except IOError as exc:
				sys.exit("Cannot open input file '{0}' : {1}".format(file_in,exc))
		
			try:
				out_file=open(file_out,"wt")
			except IOError as exc:
				sys.exit("Cannot open output file '{0}' : {1}".format(file_out,exc))
		
			no_line=0
			file_size=os.stat(file_in).st_size
			current_position=0
		
			for line in in_file.readlines():

				current_position+=len(line)
				line=line.rstrip("\r\n")

				no_line+=1
				#if (no_line< 1e5 and no_line % 1000 == 0) or (no_line<1e6 and no_line % 1e4 ==0) or (no_line>1e6 and no_line % 1e5 ==0) :
				if (no_line<1e6 and no_line % 1e4 ==0) or (no_line>1e6 and no_line % 1e5 ==0) :
					self.log_already_completed("{0} lines read from target".format(no_line),file_size,current_position)
		
				elmts = line.split("\t")
		
				if no_line == 1 :
					
					out_file.write(line)

					empty_reference=""
					if nb_max_results != 1 :
						out_file.write("\t# overlap".format(theme))
						empty_reference+="\t"
					out_file.write("\t{0} region".format(theme))
					empty_reference+="\t"

					if len(offsets)>1 :
						out_file.write("\tInterval shift")
						empty_reference+="\t"
		
					self.verify_key_columns(file_in,elmts,target_keys)
		
					#Everything is OK : read reference file now
					try:
						(header,reference_regions,annotations)=self.read_reference(file_ref,reference_keys,offsets)
						empty_reference+=re.sub("[^\t]","",header)
					except IOError as exc:
						sys.exit("Cannot open reference file '{0}' : {1}".format(file_ref,exc))
		
					if target_is_region:
						out_file.write("\t% target overlapping\t% reference overlapping")
						empty_reference+="\t\t"
					if  header != "" :
						out_file.write("\t"+header)
					out_file.write("\n")
					nb_fields=len(elmts)
					continue
		
				if no_line == 2 :
					print "Read target file"
		
				#Verify this line has the same number of fields as in header
				if len(elmts) != nb_fields:
					sys.exit("Line #"+str(no_line)+"' in '"+file_in+"' contains "+str(len(elmts))+" fields "+
						 "while header line contains "+str(nb_fields)+" fields. Exiting."
					)
				#Get genomic localisation
				if len(target_keys) == 1 :
					localisation=elmts[target_keys[0]-1]
					if localisation == "" :
						#No localisation => no overlap possible
						target_chr=""
						target_start=""
						target_end=""
					else :
						me=re.match("^(.*):([0-9]+)-([0-9]+)$",localisation)
						if me is None :
							me=re.match("^(.*):([0-9]+)$",localisation)
							if me is None :
								sys.exit("Could not interpret localisation '{0}' on line #{1} f target file {2}. Exiting.".format( \
									elmts[target_keys[0]-1],no_line,file_in) \
								)
							target_chr=me.group(1)
							target_start=int(me.group(2))
							target_end=target_start
						else :
							target_chr=me.group(1)
							target_start=int(me.group(2))
							target_end=int(me.group(3))



				else :
					target_chr = elmts[target_keys[0]-1]
			
					target_start = int(elmts[target_keys[1]-1])
					if target_is_region :
						target_end = int(elmts[target_keys[2]-1])
					else :
						target_end = target_start + 1

				target_chr = target_chr.lower().replace("chr","")
		
				if not re.match("^([0-9]+|[a-z]|mt)$",target_chr) and not keep_scaffolds :
					no_scaffolds_filtered+=1
					continue

				if target_start != "" and target_end != "" :
					if target_end < target_start:
						sys.exit("End of region before start of region in '{0}' on line #{1}.".format(file_in,no_line))
		
					target_length=(target_end-target_start+1)

		
				#Find overlaps with reference
				infos=[]
				found=False
				for offset in offsets:

					(offset,offset_label)=offset
		
					if target_chr not in reference_regions[offset] :
						break
		
					overlaps = reference_regions[offset][target_chr].find(target_start-1,target_end+1)

					if overlaps:
						valid_overlaps=[]
						for overlap in overlaps:
							offset_start=overlap.start
							offset_end=overlap.end
							offset_length=(offset_end-offset_start+1)
		
							if target_start >= offset_start:
								if target_end >= offset_end:
									overlap_length=(offset_end-target_start+1)
								else:
									overlap_length=(target_end-target_start+1)
							else:
								if target_end >= offset_end:
									overlap_length=(offset_end-offset_start+1)
								else:
									overlap_length=(target_end-offset_start+1)
		
							offset_overlap=float(overlap_length)/float(offset_length)*100
							target_overlap=float(overlap_length)/float(target_length)*100
							#print "offset_overlap={0}/{1}={2}".format(float(overlap_length),float(offset_length),offset_overlap)
							#print "target_overlap={0}/{1}={2}".format(float(overlap_length),float(target_length),target_overlap)
								
							if offset_overlap >= minimal_overlap or target_overlap >=minimal_overlap:
								reference_start=overlap.value[0]
								reference_end=overlap.value[1]
								valid_overlaps.append((offset_start,offset_end,target_overlap,offset_overlap,reference_start,reference_end))
								
						if len(valid_overlaps)!=0 :
							#Sort overlaps by % of target region overlap length
							if target_is_region :
								#sort by target overlap %, then reference overlap (both in decreasing order)
								sorted_overlaps=sorted(valid_overlaps, key=lambda ovlp: (-ovlp[2],-ovlp[3]))
							else :
								#Sort by distance between middle of target and middle of reference region
								sorted_overlaps=sorted(
									valid_overlaps,
									key=lambda ovlp:
										abs( (target_start+target_end)/2 - (ovlp[0]+ovlp[1])/2 )
								)

							no_overlap=1
							for overlap in sorted_overlaps :

								info=line
								(offset_start,offset_end,target_overlap,offset_overlap,reference_start,reference_end)=overlap
								reference_start=int(reference_start)
								reference_end=int(reference_end)
								annot=annotations[target_chr][reference_start]
		
								if nb_max_results != 1 :
									info+="\t{0}".format(no_overlap)

								info+="\t{0}:{1}-{2}".format(target_chr,reference_start,reference_end)
		
								if len(offsets)>1 :
									info+="\t{0}".format(offset_label)
		
								if target_is_region :
									info+="\t{0:.2f}%\t{1:.2f}%".format(target_overlap,offset_overlap)
		
								if annot != "" :
									info+="\t{0}".format(annot)

								infos.append(info)

								no_overlap+=1
								if nb_max_results != -1 and no_overlap > nb_max_results :
									break
							
							found=True
							break	#exit from offsets loop
				if not found :
					info=line+"\t"+empty_reference
					infos.append(info)
			
				for info in infos :
					out_file.write(info+"\n")
				
			in_file.close()
			out_file.close()
			print "\n\t{0} lines read from target in total.".format(no_line)
			if no_scaffolds_filtered != 0 :
				print "\t{0} lines not kept because keep_scaffolds is set to 'No'.".format(no_scaffolds_filtered)
		except IOError as exc:
			sys.exit("I/O error occured during annotation treatment : {1}".format(file_in,exc))
