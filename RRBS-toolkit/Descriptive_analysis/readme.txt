Usage :
-------

RRBS_HOME/Descriptive_analysis/analyse_descriptive.sh <configuration file pathname>


Configuration file structure (example in descriptive_analysis_config.txt)
------------------------------------------------------------------------

#Global parameters:
#----------------------
#title	Mono_Spz
#output_dir	./out
#
#min_samples_per_condition	2
#min_coverage	10
#max_coverage	500
#output_table_file	aggregated_methylation_results.txt
#produce_hclust	Yes
#produce_pca	Yes
#pca_scaling	Yes
#sampling_factor	0.9
Sample	File	Tissue	Colour
M1	../Differential_analysis/analysis_examples/data/MONO_1103_CPG10-500_syntheseCpG_chr1.txt	Monocyte	brown
M2	../Differential_analysis/analysis_examples/data/MONO_1130_CPG10-500_syntheseCpG_chr1.txt	Monocyte	brown
S1	../Differential_analysis/analysis_examples/data/SPZ_32j_CPG10-500_syntheseCpG_chr1.txt	Fibro	magenta
S2	../Differential_analysis/analysis_examples/data/SPZ_34j_CPG10-500_syntheseCpG_chr1.txt	Fibro	magenta

Format of the file in input :
-----------------------------
It should be the same format as the one obtained during extraction step of bismark analysis:
Chromosome	Position	Coverage	# methylated	% methylated
1	75843	12	4	25
(fields are separated by a <TAB> character)



All following parameters should be preceded by character '#' :
title				Title used to name pdf output file and header/title of the graphical produced.
output_dir			path to the directory where the pdf (and possibly table of methylation) will be produced
				(Default : "." i.e. directory from which descriptive analysis is launched)
min_coverage and max_coverage	Minimal and maximal number of reads per CpG required to take a CpG into account for the analysis.
				For a given sample and a CpG, if the coverage does not satisfy above conditions,
				its methylation proportion is set to 'NA' (this will noticeably increase Principal Component Analysis - PCA - computation).
				(Default value : 10 for min and 500 for max)
min_samples_per_condition	Minimal number of samples per group satisfying above coverage conditions.
				(Default value : no minimum)
output_table_file		Name of the file used to save methylation level table.
				If no path is specified, file will be produced into directory specified in output_dir
produce_hclust			Flag used to indicate if user wants to produce hierarchical clustering.
				(Possible values : Yes/No - Default : Yes)
produce_pca			Flag used to indicate if user wants to produce principal component analysis.
				(Possible values : Yes/No - Default : Yes)
pca_scaling			Flag indicating if data should be scaled to unit variance before computation of PCA.
				See FactoMineR documentation.
				(Possible values : Yes/No - Default : Yes)
sampling_factor			Proportion of the # of CpG satifying above conditions used to compute analysis
				This parameter is used to reduce execution time of the principal component analysis
				(Value between 0 and 1 ; Default : 1)

After these parameters you have a table with:
	name of samples which will be used for PCA and HC figures.
	pathname to the CpG data extracted by Bismark corresponding to this sample.
	name of the group of samples to which considered sample belongs
	Colour used for figures (to choose color labels, please refere to possible values in R
	(http://www.stat.columbia.edu/~tzheng/files/Rcolor.pdf)
All these values should be separated by a TAB character.

Example of coverage filters :
min_coverage=10
max_coverage=500
min_samples_per_condition=2

Suppose we have the following coverage :
	M1	M2	F1	F2
CpG1	10	12	13	10
CpG2	10	9	13	10
CpG3	10	501	13	10
CpG4	10	9	13	9

Only CpG1 will be considered for the analysis. For the other CpGs, there is at least one sample not satisfying coverage threshold and
we want to have a minimal of two samples per group satisfying coverage threshold.

