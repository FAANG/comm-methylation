# faang-methylation
This repo is to collect the FAANG methylation group's code and pipelines

It contains :
* **RRBS-Toolkit** : The RRBS-toolkit pipeline is composed of a set of scripts to analyse RRBS data, from the optimisation of experimental design up to the identification of differentially methylated regions.
Our scripts have been developed in Python 2.7, R, Shell and integrate Trim galore!, Bismark, Bowtie and Samtools.
Contact : francois.piumi@inra.fr

* **workflowbs** : This pipeline processes RRBS and WGBS data, it goes throuth all process form cleanning raw data to DRM identification and annotation. 
It has been developped in Python 3 and integrate Trim galore, FastQC, Bismark, Samtools and R script with Methylkit and DSS. 
Contact : celine.noirot@inra.fr


* **BSseeker2_RRBS_WGBS_alignment_and_calling** : This pipeline provides a set of scripts designed to provide DNA methylation calls from raw reads produced using Whole Genome Bisulfite Sequencing (WGBS) or Reduced Representation Bisulfite Sequencing (RRBS). The resulting methylation levels can be utilized for differential methylation analysis using MethylKit or other differential methylation tools. 
These scripts were developped for use with Trim galore! and BSseeker2 using Bowtie2. 
Contact : kschach2@illinois.edu
