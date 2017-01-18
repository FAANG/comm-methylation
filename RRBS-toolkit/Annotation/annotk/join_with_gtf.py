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

from gene import Gene

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

class Join_with_gtf :

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
		
	##############################################################################################################
	# read_referrence
	##############################################################################################################
	def read_reference(self,file_ref):
	
		print "Read reference ..."


		#get file size
		file_size=os.stat(file_ref).st_size

		#Parse GTF file
	        in_reference = open(file_ref)
	
		genes={}
		no_line = 0
		current_position=0
	        for gtf_line in in_reference:
			no_line = no_line + 1
			current_position+=len(gtf_line)

			#if (no_line< 1e5 and no_line % 1000 == 0) or (no_line<1e6 and no_line % 1e4 ==0) or (no_line>1e6 and no_line % 1e5 ==0) :
			if no_line % 1e5 ==0 :
				self.log_already_completed("{0} lines read from reference".format(no_line),file_size,current_position)
	
			if re.match("^#.*$",gtf_line):
				continue

	                gtf_line = gtf_line.rstrip('\r\n')
	
	                elmts = gtf_line.split('\t')
			gene_chr=elmts[0]
			gene_chr=gene_chr.lower().replace("chr","")
			start=int(elmts[3])
			end=int(elmts[4])

			if Join_with_gtf.debug and gene_chr != '1' :
				break

			feature=elmts[2]

			annot=elmts[8]
			me=re.match('^gene_id "([^"]+)".*$',annot)
			if me :
				gene_id=me.group(1)
			else :
				#Feature not related to a gene_id
				gene_id=""
				#sys.exit("Unable to find gene_id value  on line #{0} of file '{1}'. Exiting".format(no_line,file_ref))


			if feature == "gene":
				gene_start=start
				gene_end=end
				strand=elmts[6]

				if strand == "-" : strand=-1
				elif strand == '+' : strand=1
				else: sys.exit("Unexpected strand value on line #{0} of file '{1}' : '{2}'. Exiting".format(no_line,file_ref,strand))

				if gene_id not in genes :
					gene=Gene(gene_id,gene_chr,gene_start,gene_end,strand)
					genes[gene_id]=gene
				else :
					gene=genes[gene_id]
					gene.set_location(gene_chr,gene_start,gene_end)
					gene.set_strand(strand)
				#gene start and end are defined in this line, therefore we can compute :
				#tss, promoter and tss
				self.features_found["promoter"]=1
				self.features_found["tss"]=1
				self.features_found["tts"]=1
				self.features_found["gene"]=1
				gene.gene_model_has_been_defined()

			#elif feature not in("CDS","UTR","transcript") :
			else :
				if gene_id not in genes :
					gene=Gene(gene_id,gene_chr)
					genes[gene_id]=gene
				else :
					gene=genes[gene_id]
				if feature == "start_codon" :
					self.features_found["utr5"]=1
				elif feature == "stop_codon" :
					self.features_found["utr3"]=1
				elif feature == "exon" :
					self.features_found["exon"]=1
					self.features_found["intron"]=1
				else :
					self.features_found[feature.lower()]=1
				gene.add_feature(feature,start,end)

	        in_reference.close()
		print "\n\t{0} lines read from reference in total.".format(no_line)

		#Check that all features listed in configuration file has been found at least once
		for feature in self.features_found :
			if self.features_found[feature.lower()] == 0 :
				sys.stderr.write(("Warning : feature named '{0}' found in 'feature_priorities' parameter. "+
						  "This feature has never been found in reference file '{1}'.\n").format(
							feature, file_ref
				))

		#Complete feature_properties with the one found in gtf files but not requested by user
		#Otherwise when we will try to order feature overlapping with a given region
		#sorted(overlaps, key=lambda ovlp: self.feature_priorities[ ovlp.value[0] ])
		#It will raise an exception.
		for feature in self.features_found :
			if feature.lower() not in self.feature_priorities :
				self.feature_priorities[feature.lower()]=None

		#define downstream/upstream boundaries
		promoter_downstream= self.theme.get_parameter("promoter_downstream")
		promoter_upstream= self.theme.get_parameter("promoter_upstream")
		tss_downstream= self.theme.get_parameter("tss_downstream")
		tss_upstream= self.theme.get_parameter("tss_upstream")
		tts_downstream= self.theme.get_parameter("tts_downstream")
		tts_upstream= self.theme.get_parameter("tts_upstream")

		#print "promoter_upstream={0}".format(promoter_upstream)
		#print "promoter_downstream={0}".format(promoter_downstream)
		#print "tss_upstream={0}".format(tss_upstream)
		#print "tss_downstream={0}".format(tss_downstream)
		#print "tts_upstream={0}".format(tts_upstream)
		#print "tts_downstream={0}".format(tts_downstream)

		#Initialize dictionnaries
		features={}
		gene_boundaries={}

		#Build gene model
		print "Build gene model ..."
		no_gene=0
		for gene_id in genes :

			gene=genes[gene_id]
			(gene_chr,gene_start,gene_end)=gene.get_coordinates()

			no_gene+=1

			if no_gene % 1000 == 0 :
				self.log_already_completed("{0} genes treated".format(no_gene),len(genes),no_gene)

			if gene_chr not in features :
					features[gene_chr]=IntervalTree()
					gene_boundaries[gene_chr]=IntervalTree()

			if gene.gene_model_is_defined() :
				if gene_chr not in gene_boundaries :
					gene_boundaries[gene_chr]=IntervalTree()

				gene_boundaries[gene_chr].insert_interval( Interval(gene_start,gene_end, value=["gene",gene_id] ) )

				#Promoter
				if gene.strand == 1 :
					(start,end)=gene.get_promoter(promoter_upstream,promoter_downstream)
				else :
					(start,end)=gene.get_promoter(promoter_downstream,promoter_upstream)
				features[gene_chr].insert_interval( Interval(start,end, value=["promoter",gene_id] ) )
	
				#5' UTR
				(start,end)=gene.get_utr5()
				if start is not None:
					features[gene_chr].insert_interval( Interval(start,end, value=["utr5",gene_id] ) )
	
				#TTS
				if gene.strand == 1 :
					(start,end)=gene.get_tss(tss_upstream,tss_downstream)
				else :
					(start,end)=gene.get_tss(tss_downstream,tss_upstream)
				features[gene_chr].insert_interval( Interval(start,end, value=["tss",gene_id] ) )
	
				#Intron / Exon
				(intron_coords,exon_coords)=gene.get_introns_exons()

				#Debug
				#if gene.gene_id == "ENSBTAG00000000010" :
				#	print "gene_id '{0} / intron={1} / exon={2}".format(gene.gene_id,intron_coords,exon_coords)

				for exon_coord in exon_coords :
					(start,end)=exon_coord
					features[gene_chr].insert_interval( Interval(start,end, value=["exon",gene_id] ) )
	
				for intron_coord in intron_coords :
					(start,end)=intron_coord
					features[gene_chr].insert_interval( Interval(start,end, value=["intron",gene_id] ) )
	
				#TTS
				if gene.strand == 1 :
					(start,end)=gene.get_tts(tts_upstream,tts_downstream)
				else :
					(start,end)=gene.get_tts(tts_downstream,tts_upstream)
				features[gene_chr].insert_interval( Interval(start,end, value=["tts",gene_id] ) )
	
				#3' UTR
				(start,end)=gene.get_utr3()
				if start is not None:
					features[gene_chr].insert_interval( Interval(start,end, value=["utr3",gene_id] ) )
			
			#Other features
			for feature in gene.get_other_features() :
				(start,end,feature)=feature
				features[gene_chr].insert_interval( Interval(start,end, value=[feature,gene_id] ) )

		print "\n\t{0} genes treated in total.".format(no_gene)
	        return (features,gene_boundaries)
	
	##############################################################################################################
	# run_annotation
	##############################################################################################################
	def run_annotation(self,file_in,file_out) :

		theme=self.theme.get_name()
		file_ref=self.theme.get_parameter("reference_file")
		target_keys=self.theme.get_parameter("target_keys")

		keep_scaffolds=self.theme.get_parameter("keep_scaffolds").lower()
		if keep_scaffolds[0] != "n" :
			keep_scaffolds=True
		else :
			keep_scaffolds=False

		nb_max_results=self.theme.get_parameter("nb_max_results")
		max_dist_nearest_gene=self.theme.get_parameter("max_dist_nearest_gene")
	
		self.feature_priorities={}
		self.features_found={}
		no_priority=0
		for gene_feature in self.theme.get_parameter("feature_priorities").split(","):
			gene_feature=gene_feature.lower()
			no_priority+=1

			self.feature_priorities[gene_feature]=no_priority
			self.features_found[gene_feature]=0

		#there is always the feature "gene" if no other features are found
		no_priority+=1
		self.feature_priorities["gene"]=no_priority
	
		#Read input file
		target_is_region=False
		if len(target_keys)!=2 :
			target_is_region=True

		no_scaffolds_filtered=0

		#get file size
		file_size=os.stat(file_in).st_size

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
		
			current_position=0
			for line in in_file.readlines():
				line=line.rstrip("\r\n")
				current_position+=len(line)	

				no_line+=1
				#if (no_line< 1e5 and no_line % 1000 == 0) or (no_line<1e6 and no_line % 1e4 ==0) or (no_line>1e6 and no_line % 1e5 ==0) :
				if (no_line<1e6 and no_line % 1e4 ==0) or (no_line>1e6 and no_line % 1e5 ==0) :
					self.log_already_completed("{0} lines read from target".format(no_line),file_size,current_position)
		
				elmts = line.split("\t")
		
				if no_line == 1 :
					out_file.write(line)

					empty_reference=""
					if nb_max_results != 1 :
						out_file.write("\t# overlap")
						empty_reference+="\t"
					out_file.write("\tGene ID\tDistance from target\tGene feature")
					empty_reference+="\t\t"
		
					self.verify_key_columns(file_in,elmts,target_keys)
		
					#Everything is OK : read reference file now
					try:
						(features,gene_boundaries)=self.read_reference(file_ref)
					except IOError as exc:
						sys.exit("Cannot open reference file '{0}' : {1}".format(file_ref,exc))

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
							sys.exit("Could not interpret localisation '{0}' on line #{1} f target file {2}. Exiting.".format( \
								elmts[target_keys[0]-1],no_line,file_in) \
							)
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


				#Find overlaps with gene features
				overlaps=[]

				if target_chr in features :
					overlaps.extend(features[target_chr].find(target_start-1,target_end+1))
					#Look if inside gene : may happen if gene has no other definition than gene_start and end (no exon features)
					overlaps.extend(gene_boundaries[target_chr].find(target_start-1,target_end+1))
		

				at_least_one_result_found=False
				if len(overlaps)!=0 :
					no_overlap=1
					treated={}
					for overlap in sorted(overlaps, key=lambda ovlp: self.feature_priorities[ ovlp.value[0].lower() ])  :
						gene_feature=overlap.value[0]

						if gene_feature == "gene" and len(overlaps) != 1 :
							continue

						if self.feature_priorities[gene_feature.lower()] is None :
							#Not requested by user
							continue
						#At this step, we will output at least one result
						at_least_one_result_found=True

						gene_id=overlap.value[1]

						#output only once for a couple of {gene_feature;gene_id}
						if "{0}\t{1}".format(gene_id,gene_feature) in treated :
							continue
						treated["{0}\t{1}".format(gene_id,gene_feature)]=1

						if nb_max_results!=1 :
							out_file.write("{0}\t{1}\t{2}\t{3}\t{4}\n".format(
								line,
								no_overlap,gene_id,0,gene_feature
							))
						else :
							out_file.write("{0}\t{1}\t{2}\t{3}\n".format(
								line,
								gene_id,0,gene_feature
							))
						no_overlap+=1
						if nb_max_results != -1 and no_overlap > nb_max_results :
							break

				if not at_least_one_result_found :
					gene_id=min_dist=gene_feature=""
					no_overlap=1
					if target_chr in gene_boundaries :

						#Look for nearest gene
						next_upstream_gene=gene_boundaries[target_chr].upstream_of_interval(
										Interval(target_start,target_end),max_dist=max_dist_nearest_gene
						)
						if len(next_upstream_gene) != 0 :
							dist_upstream=target_start - next_upstream_gene[0].end
							assert dist_upstream > 0, \
							"Negative distance found between region {0}:{1}-{2} and next upstream gene '{3}' {0}:{4}-{5}.".format(
								target_chr,target_start,target_end,
								next_upstream_gene[0].value[1], next_upstream_gene[0].start, next_upstream_gene[0].end
							)
						else :
							dist_upstream=None
	
						next_downstream_gene=gene_boundaries[target_chr].downstream_of_interval(
										Interval(target_start,target_end),max_dist=max_dist_nearest_gene
						)
						if len(next_downstream_gene) != 0 :
							dist_downstream=next_downstream_gene[0].start - target_end
							assert dist_downstream > 0, \
							"Negative distance found between region {0}:{1}-{2} and next downstream gene '{3}' {0}:{4}-{5}.".format(
								target_chr,target_start,target_end,
								next_downstream_gene[0].value[1], next_downstream_gene[0].start, next_downstream_gene[0].end
							)
						else :
							dist_downstream=None

						if dist_upstream is not None and dist_downstream is not None :
							if dist_upstream<dist_downstream :
								gene_id=next_upstream_gene[0].value[1]
								min_dist="+{0}".format(dist_upstream)
							else :
								gene_id=next_downstream_gene[0].value[1]
								min_dist="-{0}".format(dist_downstream)
						elif dist_upstream is not None :
							gene_id=next_upstream_gene[0].value[1]
							min_dist="+{0}".format(dist_upstream)
						elif dist_downstream is not None :
							gene_id=next_downstream_gene[0].value[1]
							min_dist="-{0}".format(dist_downstream)
						else :
							no_overlap=""
					#else :
						#print "No chr '{0}' in gene_boundaries dictionnary.".format(target_chr)

					if nb_max_results != 1 :
						out_file.write("{0}\t{1}\t{2}\t{3}\t{4}\n".format(
							line,
							no_overlap,gene_id,min_dist,gene_feature
						))
					else :
						out_file.write("{0}\t{1}\t{2}\t{3}\n".format(
							line,
							gene_id,min_dist,gene_feature
						))

			in_file.close()
			out_file.close()
			print "\n\t{0} lines read from target in total.".format(no_line)
			if no_scaffolds_filtered != 0 :
				print "\t{0} lines not kept because keep_scaffolds is set to 'No'.".format(no_scaffolds_filtered)

		except IOError as exc:
			sys.exit("I/O error occured during annotation treatment : {1}".format(file_in,exc))


#if __name__ == "__main__":
#	join=Join_with_gtf(None)
#	join.read_reference("reference/Bos_taurus.UMD3.1.81.gtf",[1,4,5])

