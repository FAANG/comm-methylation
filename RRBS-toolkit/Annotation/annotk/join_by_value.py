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
import sys
from sys import argv
import re

class Join_by_value :

	debug=True

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
	
	def read_reference(self,file_ref,reference_keys):
	
		print "Read reference ..."
	        annotations = {}
	
	        in_reference = open(file_ref)
		file_size=os.stat(file_ref).st_size
	
		no_line = 0
		current_position = 0
	        for line_annot in in_reference:

			current_position+=len(line_annot)
			no_line = no_line + 1

			#if (no_line< 1e5 and no_line % 1000 == 0) or (no_line<1e6 and no_line % 1e4 ==0) or (no_line>1e6 and no_line % 1e5 ==0) :
			if no_line % 1e5 ==0 :
				self.log_already_completed("{0} lines read from reference".format(no_line),file_size,current_position)
	
	                line_annot = line_annot.rstrip('\r\n')
	
	                elmts = line_annot.split('\t')
	
	                if no_line == 1:
	                        header=""

	                        self.verify_key_columns(file_ref,elmts,reference_keys)

				skip={}
				no_field=0
	                        for i in range(0,len(elmts)):
	                                #part of reference_keys ?
	                                skip[i]=False
	                                for j in range(0,len(reference_keys)) :
	                                        if i+1 == reference_keys[j] :
	                                                skip[i]=True
	                                                break
	                                if skip[i] :
	                                        continue
					no_field+=1
	                                if no_field != 1 :
	                                        header+="\t"
	                                header+=elmts[i]
	                                nb_fields = len(elmts)
	                        continue
	
			#Verify # of fields is the same as in header
			if len(elmts) != nb_fields:
				sys.exit("Line #"+str(no_line)+"' in '"+file_ref+"' contains "+str(len(elmts))+" fields "+
					 "while header line contains "+str(nb_fields)+" fields. Exiting."
				)
	
			#Get key value
			key=""
			for i in range(0,len(reference_keys)) :
				if i != 0 :
					key+="\t"
				key+=elmts[reference_keys[i]-1]

			if key in annotations :
				sys.exit("There are several lines in reference file with key value '{0}'. Exiting.".format(key))
	
	                #Keep extra informations
	                annotations[key]=""
			no_field=0
	                for i in range(0,len(elmts)):
	                        if skip[i] :
	                                continue
				no_field+=1
	                        if no_field != 1 :
	                                annotations[key]+="\t"
	                        annotations[key]+=elmts[i]
	
	        in_reference.close()
		print "\n\t{0} lines read from reference in total.".format(no_line)
	        return header, annotations
	
	def run_annotation(self,file_in,file_out) :

		theme=self.theme.get_name()
		file_ref=self.theme.get_parameter("reference_file")
		target_keys=self.theme.get_parameter("target_keys")
		reference_keys=self.theme.get_parameter("reference_keys")

		#Read input file
		try:
			try:
				in_file=open(file_in,"rt")
			except IOError as exc:
				sys.exit("Cannot open input file '{0}' : {1}".format(file_in,exc))
		
			try:
				out_file=open(file_out,"wt")
			except IOError as exc:
				sys.exit("Cannot open output file '{0}' : {1}".format(file_out,exc))
		
			file_size=os.stat(file_in).st_size

			no_line=0
			current_position=0

			for line in in_file.readlines():

				current_position+=len(line)
				line=line.rstrip("\r\n")
		
				no_line+=1
				#if (no_line< 1e5 and no_line % 1000 == 0) or (no_line<1e6 and no_line % 1e4 ==0) or (no_line>1e6 and no_line % 1e5 ==0) :
				if no_line % 1e5 ==0 :
					self.log_already_completed("{0} lines read from target".format(no_line),file_size,current_position)
		
				elmts = line.split("\t")
		
				if no_line == 1 :
					out_file.write(line)
					empty_reference=""
		
					self.verify_key_columns(file_in,elmts,target_keys)
		
					#Everything is OK : read reference file now
					try:
						(header,annotations)=self.read_reference(file_ref,reference_keys)
						empty_reference+=re.sub("[^\t]","",header)
					except IOError as exc:
						sys.exit("Cannot open reference file '{0}' : {1}".format(file_ref,exc))
		
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
				#Get key value
				key=""
				for i in range(0,len(target_keys)) :
					if i != 0 :
						key+="\t"
					key+=elmts[target_keys[i]-1]
		
		
				#Find overlaps with reference
				info=line
				if key in annotations :
					info+="\t"+annotations[key]
				else :
					info+="\t"+empty_reference
			
				out_file.write(info+"\n")
				
			in_file.close()
			out_file.close()
			print "\n\t{0} lines read from target in total.".format(no_line)
		except IOError as exc:
			sys.exit("I/O error occured during annotation treatment : {1}".format(file_in,exc))
