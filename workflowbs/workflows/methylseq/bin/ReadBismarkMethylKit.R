
if (!("methylKit" %in% rownames(installed.packages()))) {
	install.packages( c("data.table","devtools"),  repos="http://cran.univ-paris1.fr")
	source("http://bioconductor.org/biocLite.R")
	biocLite(c("GenomicRanges","IRanges"))
	library(devtools)
	install_github("al2na/methylKit",build_vignettes=FALSE)
	
}
if (!("optparse" %in% rownames(installed.packages()))) {
	install.packages("optparse", repos="http://cran.univ-paris1.fr")
}

suppressPackageStartupMessages(library("optparse"))
suppressPackageStartupMessages(library("methylKit"))



library(optparse)
library(methylKit)

option_list = list(
		make_option(c("-f", "--sam"), type="character", default=NULL, 
				help="Read sam for generate a methylation calling file for each sample in directory [default= %default]", metavar="character"),
		make_option(c("-R", "--reference"), type="character", default=FALSE, 
				help="Genome assembly [default %default]", metavar="character"),
		make_option(c("-c", "--context"), type="character", default=FALSE, 
				help="Methylation context [default %default]", metavar="character"),
		make_option(c("-m", "--mincoverage"), type="integer", default=FALSE, 
				help="Minimum of coverage [default %default]", metavar="number"),
		make_option(c("-o", "--out"), type="character", default=NULL, 
				help="output file name [default= %default]", metavar="character")
); 

opt_parser = OptionParser(option_list=option_list)
opt = parse_args(opt_parser)

read.bismark(location = opt$sam, sample.id = substr(basename(opt$sam), 1, nchar(basename(opt$sam)) - 4), assembly = opt$reference, read.context = opt$context, mincov = opt$mincoverage, save.folder = dirname(opt$out))





