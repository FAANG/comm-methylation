Set of scripts to analyse RRBS data, from the optimisation of experimental design up to the identification of differentially methylated regions
=======

Our pipeline is a comprehensive set of tools allowing to conduct RRBS analysis, from the optimisation of experimental design, up to the identification of differentially methylated regions DMRs between two groups of samples.

<H1>Organisation of scripts</H1>

Main steps of the pipeline are organized in following directories :

<H2>RR_genome</H2>
Directory contains a script to simulate *in silico* fragmentation of the genome after digestion by a restriction enzyme (ex : MSP1) and selection of fragments. Fragments selected are stored in a fasta file. This fasta files can be annotated in a further step (see **Annotation**), to produce a table showing in which gene or genomic feature a fragment is located.

<H2>Bismark_methylation_call</H2>
Directory contains scripts to prepare the genome for Bismark mapping and to process fastq files.	
At the end of the process of fastq files, this pipeline provide a file (**synthese_CpG.txt**) containing the coverage and the percentage of methylation for each CpG at least covered by one read.

<H2>Descriptive_analysis</H2>
Directory contains a script to produce a hierarchical clustering and principal component analyses of several samples.

<H2>Differential analysis</H2>
Directory contains a script to compare methylation of two groups of samples, either using [methylKit](https://bioconductor.org/packages/devel/bioc/vignettes/methylKit/inst/doc/methylKit.html) or [methylSig](http://sartorlab.ccmb.med.umich.edu/node/17) R package.

<H2>Annotation</H2>
Directory contains a script to annotate results of RR_genome or differential analysis.

<H2>Venn</H2>
Directory contains a script to compare 2 or 3 analysis results.

In each one of these directories, you will find a dedicated readme file (in pdf format) describing the main goals of the step and how to use scripts.

Schema describing the relationships existing between the main modules:
![RRBS toolkit schema](https://github.com/ljouneau/RRBS-toolkit/blob/master/RRBBS_toolkit_schema.png)

<H1>Technical prerequisites</H1>

Our scripts have been developped in :
* Python 2.7 (with bx.intervals.intersection module for the Annotation and matplotlib for the Venn)
* R (version >= 3.30)
* Shell

It integrates several external tools :
* [Trim galore!](http://www.bioinformatics.babraham.ac.uk/projects/trim_galore/)
* [Bismark](http://www.bioinformatics.babraham.ac.uk/projects/bismark)
* [Bowtie](http://bowtie-bio.sourceforge.net/index.shtml)
* [samtools](http://samtools.sourceforge.net/)

All these tools should be installed before to use RRBS toolkit.

Once all these prerequisites are satisfied, you should edit file **RRBS_HOME/config.sh** and change the path to these external tools (**RRBS_HOME** referes to the path where RRBS toolkit is installed).

