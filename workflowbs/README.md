# 1 - What is workflowBS ?
  
  workflowBS is an application based on Jflow (full documentation 
  available http://genoweb.toulouse.inra.fr:8090/app/index.html)
  This application was design to process bisulfite data (wgbs or rrbs / 
  single and paired reads).
  To do so, this application
  - index the reference genome - Bismark (if not available)
  - clean data - trim_galore
  - run fastqc before and after cleaning
  - align reads on a reference and/or a control genome - Bismark
  - remove duplicates if the data are not rrbs - samtools
  - extract methylation - methylKit (use perl script of methylkit)
  - remove SNP positions - home-made script (during statistics preprocess)
  - research DMC - methylKit or DSS
  - research DMR - with eDMR for methylkit or DSS for DMC found with DSS
  - Compute full of graphics to exploit results
  For the moment, the pipeline is only available from command line even
  if Jflow provides a web server mode.

# 2 - Installation

## a - Prerequists

  * Python: the supported versions are 3.2 or higher. 
  * Makeflow: a workflow engine for executing large complex workflows on 
  clusters, clouds, and grids. The supported version is v4.4.3. 
  http://ccl.cse.nd.edu/software/files/cctools-4.4.3-source.tar.gz

  * FastQC >= v0.11.2
  * Trim_galore v0.4
  * Bismark 1.15
  * Bowtie 1 or Bowtie 2
  * R 3.2.2 or higher (If you run statistical tests)
	* IMPORTANT for clusters: if packages are not available, the script automatically install it 
		but note that if you are on a cluster the R_LIBS environment variable must
		be set to an existing directory located in your home directory 
		home directory. (export R_LIBS="~/save/Rlib"; mkdir ~/save/Rlib)

## b - Download source	
	git clone https://github.com/FAANG/faang-methylation.git
	cd faang-methylation/workflowbs

Follow the instructions in the README.md file (this file ;) )
	
## c - Install R package
To install R package (with version of R > 3.2.2) you can run the scripts :
 * Rscript faang-methylation/workflowbs/workflows/methylseq/bin/install_r_package_for_dss.R
 * Rscript faang-methylation/workflowbs/workflows/methylseq/bin/install_r_package_for_methylkit.R

Use Methylkit V 0.9.6 !!

Note : eDmr is no more available at CRAN, so the DMR cannot be found with Methylkit results.

# 3 - Configuration

Edit the application.properties file to configure the application, instructions
are embedded within the file (faang-methylation/workflowbs/application.properties)

For advanced configuration please refer to the online documentation [http://genoweb.toulouse.inra.fr:8090/app/jflow_advanced_configuration.html]
	
# 4 - Test your installation

From directory faang-methylation/workflowbs launch :
## To display the global help :
    python3 ./bin/jflow_cli.py methylseq --help
    
    usage: jflow_cli.py methylseq [-h] --reference-genome REFERENCE_GENOME
                              [--control-genome CONTROL_GENOME]
                              [--snp-reference SNP_REFERENCE]
                              [--annotation ANNOTATION] [--tss TSS] --sample
                              INPUT_SAMPLE [INPUT_SAMPLE ...] [--is-single]
                              [--rrbs] [--non-directional] [--phred64]
                              [--quality QUALITY]
                              [--alignment-mismatch ALIGNMENT_MISMATCH]
                              [--max-insert-size MAX_INSERT_SIZE] [--bowtie1]
                              [--no-rmdup]
                              [--deduplicate-with {bismark,samtools}]
                              [--coverage COVERAGE] [--context {CpG,CHG,CHH}]
                              [--no-overlap]
                              [--test-methylkit TEST_METHYLKIT [TEST_METHYLKIT ...]]
                              [--test-dss TEST_DSS [TEST_DSS ...]]

    optional arguments:
    -h, --help            show this help message and exit
     --is-single           IF BAM PROVIDED : Set true if you provide alignment of
                        single-end library

    Input files:
    --reference-genome REFERENCE_GENOME
                        Which genome should the read being align on
    --control-genome CONTROL_GENOME
                        Control reference sequence
    --snp-reference SNP_REFERENCE
                        VCF file of known SNP to remove from the analysis
    --annotation ANNOTATION
                        annotation file (gff ot gtf files), used in DMC
                        categorization
    --tss TSS             file with TSS positions (files format: chr tss
                        strand), used to plot methylation level around TSS

    Sample description:
    --sample INPUT_SAMPLE [INPUT_SAMPLE ...]
                        Definition of a sample (methylkit=<INPUTFILE>,
                        read2=<INPUTFILES>, sample-name=<STR>,
                        read1=<INPUTFILES>, bam=<INPUTFILE>)

    Protocol parameters:
    --rrbs                Workflow for RRBS data : clean data (MspI digested
                        material) and do not perform rmdup
    --non-directional     To set if the libraries are non directional (Default :
                        False)
    --phred64             Quality scores phred64 scale used otherwise phred33 is
                        the default

    Cleaning parameters:
    --quality QUALITY     Quality threshold to trim low-quality ends from reads
                        in addition to adapter removal

    Bismark alignment parameters:
    --alignment-mismatch ALIGNMENT_MISMATCH
                        Sets the number of mismatches to allowed in a seed
                        alignment during multi-seed alignment
    --max-insert-size MAX_INSERT_SIZE
                        The maximum insert size for valid paired-end
                        alignments.
    --bowtie1             Use bowtie1 instead of bowtie2 (longer, better for
                        reads < 50bp) - default False
    --no-rmdup            Force to not perform rmdup
    --deduplicate-with {bismark,samtools}
                        Perform deduplication with dedulicate_bismark or
                        samtools

    Methylation extraction parameters:
    --coverage COVERAGE   Minimum read coverage
    --context {CpG,CHG,CHH}
                        Type of methylation context to extract and analyze
    --no-overlap          The overlapping paired reads will be ignored during
                        extraction step

    DMC parameters with methylKit :
    --test-methylkit TEST_METHYLKIT [TEST_METHYLKIT ...]
                        Which test should be used for differential methylation
                        analysis (pool1=<STR>, pool2=<STR>, dmr=<BOOL>, num-
                        dmc=<INT>, filter=<BOOL>, stranded=<BOOL>,
                        correct=<STR>, normalization=<BOOL>, test-name=<STR>,
                        num-c=<INT>, alpha=<FLOAT>, feature=<STR>)

    DMC/DMR parameters with DSS:
    --test-dss TEST_DSS [TEST_DSS ...]
                        Which test should be used for differential methylation
                        analysis (pool1=<STR>, pool2=<STR>, low-cov=<INT>,
                        dmr=<BOOL>, correct=<STR>, normalization=<STR>, test-
                        name=<STR>, high-cov=<INT>, num-c=<INT>,
                        alpha=<FLOAT>, feature=<STR>, prop-dmc=<FLOAT>)





# 5 - Run a workflow

You can run a test workflow by using the command line parameters or by using a configuration
file. A configuration file example is given in workflows/methylseq/data/test_wgbs_paired.conf.


## Using the configuration file, the corresponding command line is :

    python3 ./bin/jflow_cli.py methylseq @workflows/methylseq/data/test_wgbs_paired.conf

## Using parameters, the command line is :

    python3 ./bin/jflow_cli.py methylseq --reference-genome workflows/methylseq/data/Gallus_gallus.Galgal4.dna.chromosome.7.fa \
    --snp-reference workflows/methylseq/data/snp.vcf \
    --sample sample-name=sample1 read1=workflows/methylseq/data/sample1.R1.fastq.gz read2=workflows/methylseq/data/sample1.R2.fastq.gz \
    --sample sample-name=sample2 read1=workflows/methylseq/data/sample2.R1.fastq.gz read2=workflows/methylseq/data/sample2.R2.fastq.gz \
    --sample sample-name=sample3 read1=workflows/methylseq/data/sample3.R1.fastq.gz read2=workflows/methylseq/data/sample3.R2.fastq.gz \
    --sample sample-name=sample4 read1=workflows/methylseq/data/sample4.R1.fastq.gz read2=workflows/methylseq/data/sample4.R2.fastq.gz \
    --sample sample-name=sample5 read1=workflows/methylseq/data/sample5.R1.fastq.gz read2=workflows/methylseq/data/sample5.R2.fastq.gz \
    --sample sample-name=sample6 read1=workflows/methylseq/data/sample6.R1.fastq.gz read2=workflows/methylseq/data/sample6.R2.fastq.gz \
    --sample sample-name=sample7 read1=workflows/methylseq/data/sample7.R1.fastq.gz read2=workflows/methylseq/data/sample7.R2.fastq.gz \
    --sample sample-name=sample8 read1=workflows/methylseq/data/sample8.R1.fastq.gz read2=workflows/methylseq/data/sample8.R2.fastq.gz \
    --coverage 5  --context CpG \
    --test-methylkit test-name=sex pool1=sample1,sample4,sample5,sample8 pool2=sample2,sample3,sample6,sample7 normalization=1 filter=1 correct=BH alpha=0.05 

# 6 - Errors

Get the id of your workflow with

    python3 bin/jflow_cli.py status 

If your workflow failed, please try the command:

    python3 bin/jflow_cli.py status --workflow-id VALUE --errors

You will get the command line which failed and have access to the stderr file.
Example :

      Failed Commands :
      - MethylKitExtractor.CpG :
        /work/user/JflowSvn/work/methylseq/wf000001/.working/6b2330a007/_Stash/0/0/0/w000001B /work/fescudie/JflowSvn/work/methylseq/wf000001/SamtoolsSortSam_default/sample2_clean.sam /work/fescudie/JflowSvn/work/methylseq/wf000001/MethylKitExtractor_CpG/sample2_clean_CpG.txt /work/fescudie/JflowSvn/work/methylseq/wf000001/MethylKitExtractor_CpG/sample2_clean_CpG.stderr
    
# 7 - Support
The person in charge of support leave the team, no more support on this application (July 2016)
Support is available by email at support.genopole@toulouse.inra.fr
