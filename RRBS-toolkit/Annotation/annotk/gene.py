import re
import sys

"""
	Class used to store and compute gene features boundaries
"""
class Gene :

	def __init__(self,gene_id,gene_chr=None,gene_start=None,gene_end=None,strand=1) :
		self.gene_id=gene_id
		self.set_location(gene_chr,gene_start,gene_end)
		self.set_strand(strand)
		self.gene_model_defined=False
		self.features={}

	def gene_model_has_been_defined(self) :
		self.gene_model_defined=True
		
	def gene_model_is_defined(self) :
		return self.gene_model_defined
		
	def set_location(self,gene_chr,gene_start,gene_end) :
		self.gene_chr=gene_chr
		self.gene_start=gene_start
		self.gene_end=gene_end

	def set_strand(self,strand) :
		assert strand in [1,-1], "Invalid value '{0}' for strand in gene '{1}'.".format(strand,self.gene_id)
		self.strand=strand

	def add_feature(self,feature,start,end) :
		if feature not in self.features :
			self.features[feature]=[]
		self.features[feature].append((start,end))

	def get_coordinates(self) :
		return (self.gene_chr,self.gene_start,self.gene_end)

	def get_promoter(self,upstream_offset=0,downstream_offset=0) :
		if self.strand == 1 :
			start=self.gene_start-upstream_offset
			end=self.gene_start+downstream_offset
		else :
			start=self.gene_end-upstream_offset
			end=self.gene_end+downstream_offset
		return (start,end)

	def get_tss(self,upstream_offset=0,downstream_offset=0) :
		if self.strand == 1 :
			start=self.gene_start-upstream_offset
			end=self.gene_start+downstream_offset
		else :
			start=self.gene_end-upstream_offset
			end=self.gene_end+downstream_offset
		return (start,end)

	def get_utr5(self) :
		if "start_codon" not in self.features :
			return (None,None)

		if self.strand == 1 :
			#get the most upward start codon
			reverse_sort=False
		else :
			#get the most forward start codon
			reverse_sort=True

		#Get the first element from sorted list
		start_codon=sorted(self.features["start_codon"], key= lambda sc : sc[0], reverse=reverse_sort)[0]
		#print "start_codon={0} / gene_start=[{1};{2}] / strand={3} /".format(start_codon,self.gene_start,self.gene_end,self.strand)

		if self.strand==1 and start_codon[0]==self.gene_start :
			return (None,None)
		if self.strand==-1 and start_codon[1]==self.gene_end :
			return (None,None)

		if self.strand == 1 :
			start=self.gene_start
			end=start_codon[0]-1
		else :
			start=start_codon[1]+1
			end=self.gene_end
		return (start,end)

	def get_utr3(self) :
		if "stop_codon" not in self.features :
			return (None,None)

		if self.strand == 1 :
			#get the most forward start codon
			reverse_sort=False
		else :
			#get the most upward start codon
			reverse_sort=True

		#Get the first element from sorted list
		stop_codon=sorted(self.features["stop_codon"], key= lambda sc : sc[0], reverse=reverse_sort)[-1]
		#print "stop_codon={0} / gene_start=[{1};{2}] / strand={3} /".format(stop_codon[1],self.gene_start,self.gene_end,self.strand)
		if self.strand==1 and stop_codon[1]==self.gene_end :
			return (None,None)
		if self.strand==-1 and stop_codon[0]==self.gene_start :
			return (None,None)

		if self.strand == 1 :
			start=stop_codon[1]+1
			end=self.gene_end
		else :
			start=self.gene_start
			end=stop_codon[0]-1
		return (start,end)

	def _get_exons(self) :
		coding_exons=[]
		if "exon" not in self.features :
			#no exon feature defined but there are start and stop codons
			if "start_codon" in self.features and "stop_codon" in self.features :
				if self.strand == 1 :
					#get the most forward start codon
					reverse_sort=False
				else :
					#get the most upward start codon
					reverse_sort=True
		
				#Get the first element from sorted list
				start_codon=sorted(self.features["start_codon"], key= lambda sc : sc[0], reverse=reverse_sort)[0]
				stop_codon=sorted(self.features["stop_codon"], key= lambda sc : sc[0], reverse=reverse_sort)[-1]
				if not reverse_sort :
					start=start_codon[0]
					end=stop_codon[1]
				else :
					start=stop_codon[0]
					end=start_codon[1]

				assert start<=end, "No coding exons defined for '{0}' - strand={1} - but start > end".format(self.gene_id,self.strand)
				coding_exons.append((start,end))
			return coding_exons

		exons=sorted(self.features["exon"],key=lambda ex : ex[0])
		
		#get rid off UTR exons
		(start_utr3,end_utr3)=self.get_utr3()
		(start_utr5,end_utr5)=self.get_utr5()

		#get tts and tts
		tss=self.get_tss()[0]
		tts=self.get_tts()[0]

		debug=0
		if self.gene_id == "ENSBTAG00000012785" :
			debug=1

		for exon in exons :
			(start,end)=exon

			error_message=("Unexpected exon boundaries. exon=[{0};{1}] / UTR5=[{2};{3}] / UTR3=[{4};{5}] "+
				       "/ TSS={6} / TTS={7} / Strand={8} / Gene={9}."
			).format(
				start,end, start_utr5,end_utr5, start_utr3,end_utr3, tss, tts, self.strand, self.gene_id
			)

			if (start>=start_utr3 and end<=end_utr3) or (start>=start_utr5 and end<=end_utr5) : 
				#exon in UTR
				continue
			if self.strand==1 :
				#Forward gene
				if end_utr5 is not None and start<=end_utr5 :
					#exon partially in 5'UTR
					assert end > end_utr5, error_message
					coding_exons.append((end_utr5,end))
				elif start_utr3 is not None and end>=start_utr3 :
					#exon partially in 3'UTR
					assert start_utr3 is None or start < start_utr3, error_message
					coding_exons.append((start,start_utr3))
				else :
					#Coding exon
					assert end_utr5 is None or start>end_utr5, error_message
					assert start_utr3 is None or end<start_utr3, error_message
					coding_exons.append((start,end))
			else :
				#Reverse gene
				if start_utr5 is not None and end>=start_utr5 :
					#exon partially in 5'UTR
					assert start_utr5 is None or start < start_utr5, error_message
					coding_exons.append((start,start_utr5))
				elif end_utr3 is not None and start<=end_utr3 :
					#exon partially in 3'UTR
					assert end_utr3 is None or end>end_utr3, error_message
					coding_exons.append((end_utr3,end))
				else :
					#Coding exon
					assert end_utr3 is None or start>end_utr3, error_message
					assert start_utr5 is None or end<start_utr5, error_message
					coding_exons.append((start,end))

		#Treat overlapping and adjacent exons
		exons=sorted(coding_exons, key=lambda ex: ex[0])
		coding_exons=[]
		for exon in exons :
			(start,end)=exon
			if len(coding_exons)!=0 :
				(last_start,last_end)=coding_exons[-1]

				if start == last_start and end == last_end :
					continue


				if start<=last_end+1: #Overlaps with previous exons (if start==last_end+1, exons are adjacent)
					new_start=min(start,last_start)
					new_end=max(end,last_end)
					coding_exons[-1]=(new_start,new_end)
					continue
			coding_exons.append((start,end))

		return coding_exons

	def get_introns_exons(self) :
		coding_exons=self._get_exons()

		introns=[]
		last_exon_end=None

		debug=0
		if self.gene_id == "ENSBTAG000000XXXXX" :
			debug=1

		for exon in sorted(coding_exons, key=lambda ce: ce[0]) :
			if debug :
				print "Exon [{0},{1}]".format(exon[0],exon[1])

			if last_exon_end is not None :
				if last_exon_end+1 >= exon[0]-1 and debug :
					print "Intron [{0},{1}] - gene_id={2}".format(last_exon_end+1,exon[0]-1,self.gene_id)
				introns.append((last_exon_end+1,exon[0]-1))
			last_exon_end=exon[1]
		return (introns,coding_exons)

	def get_tts(self,upstream_offset=0,downstream_offset=0) :
		if self.strand == 1 :
			start=self.gene_end-upstream_offset
			end=self.gene_end+downstream_offset
		else :
			start=self.gene_start-downstream_offset
			end=self.gene_start+upstream_offset
		return (start,end)

	def get_other_features(self) :
		other_features=[]
		for feature in self.features :
			if feature in ("promoter","tss","utr5","utr3","intron","exon","tts","UTR","start_codon","stop_codon") :
				continue

			for interval in self.features[feature] :
				(start,end)=interval
				other_features.append((start,end,feature))

		return other_features
"""
	End of definition of Gene class
"""

