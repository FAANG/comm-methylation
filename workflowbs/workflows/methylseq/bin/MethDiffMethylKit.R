######### Analysis of DNA methylation data (with methylKit package) ############
################################################################################


### ---------------------Packages

# if package is installed locally, load
if (!("optparse" %in% rownames(installed.packages()))) {
  install.packages(package, repos="http://cran.univ-paris1.fr")
}
library("optparse")

#methylKit package
if (!("methylKit" %in% rownames(installed.packages()))) {
  source("http://bioconductor.org/biocLite.R") 
  biocLite(c("GenomicRanges","IRanges"))
  
  if (!("devtools" %in% rownames(installed.packages()))) {
    install.packages("devtools", repos = "http://cran.univ-paris1.fr")
  }
  library(devtools)
  install_github("al2na/methylKit", build_vignettes = FALSE)
}
library(methylKit)


### ---------------------Parameters

#############
###### Parameter initialization when the script is launched from command line
############
option_list = list(
  make_option(c("-d", "--directory"), type = "character", default = NULL, 
              help = "name of the directory where all files are stored", 
              metavar = "character"),
  make_option(c("-f", "--files"), type = "character", default = NULL, 
              help = "list of files path and name separated by ','", 
              metavar = "character"),
  make_option(c("-R", "--reference"), type="character", default=NULL, 
              help="Reference genome name ", metavar="character"),
  make_option(c("-c", "--context"), type="character", default="CpG", 
              help="Methylation context [CpG,CHH,CHG,none]", metavar="character"),
  make_option(c("--pool1"), type = "character", default = NULL,
              help = "library name in pool 1 separated by ', '", 
              metavar = "character"),
  make_option(c("--pool2"), type = "character", default = NULL,
              help = "library name in pool 2 separated by ', '", 
              metavar = "character"),
  make_option(c("--normalization"), type = "logical", default = FALSE,
              help = "if TRUE a median normalization on coverage is performed
              [default=%default]", metavar = "character"),
  make_option(c("--filter"), type = "logical", default = FALSE,
              help = "if TRUE a filter for low and high coverage is applied
              [default=%default]", metavar = "character"),
  make_option(c("--alpha"), type = "double", default = 0.05,
              help = "significance level of the tests (i.e. acceptable rate of 
              false-positive in the list of DMC) 
              [default=%default]", 
              metavar = "character"),
  make_option(c("--correct"), type = "character", default = "BH",
              help = "method used to adjust p-values for multiple testing 
              ('BH' or 'bonferroni') [default=%default]", metavar = "character"),
  make_option(c("-o", "--out"), type = "character", default = NULL, 
              help = "output file path where results are stored", 
              metavar = "character")
  )

opt_parser = OptionParser(usage="Imports data and find DMC.", 
                          option_list = option_list)

opt = parse_args(opt_parser)

#file names are needed to continue
if ((is.null(opt$files) & is.null(opt$directory)) | is.null(opt$out)) {
  print_help(opt_parser)
  stop("files or results directory missing.\n", call. = FALSE)
}

#pools are needed to continue
if (is.null(opt$pool1) | is.null(opt$pool2)) {
  print_help(opt_parser)
  stop("pools are necessary.\n", call. = FALSE)
}





#####################################################
### ---------------------Input data and preprocessing
#####################################################

#vector of path and filenames
filenames <- NULL
if (!is.null(opt$directory)){
  filenames <- dir(opt$directory)
  filenames <- filenames[regexpr(pattern = ".txt", filenames, fixed = TRUE) != -1]
  l <- normalizePath(file.path(opt$directory, filenames), mustWork = FALSE)
} else {
  l <- unlist(strsplit(opt$files, ','))
  for(i in seq_along(l)){
    filenames[i] <- tail(unlist(strsplit(l[i], '/')), n=1)
  }
}

#pool: compare list in opt$pool1 and opt$pool2 with names
pool1 <- unlist(strsplit(opt$pool1, ','))
pool2 <- unlist(strsplit(opt$pool2, ','))
pool <- c(pool1, pool2)

for(i in seq_along(pool)){
  if(!(pool[i] %in% filenames)){
    stop("pools and files not match.\n", call. = FALSE)
  }  
}


#####################################################
### -------------------------------DMC with methylKit
#####################################################

#Input raw data
meth_data <- read(as.list(l), sample.id = as.list(filenames), assembly = opt$reference,
                treatment = ifelse(filenames %in% pool1, 1, 0),
                context = opt$context)

#normalization
if(opt$normalization){
  meth_data <- normalizeCoverage(meth_data, method = "median")
}

#filter
if(opt$filter){
  meth_data <- filterByCoverage(meth_data, lo.count = 5, hi.perc = 99)
}


#perform the test
meth_data <- unite(meth_data, destrand = FALSE)
res_test <- calculateDiffMeth(meth_data, slim = FALSE, weighted.mean = FALSE)
res <- getData(res_test)

#change p-value correction if it's not "BH"
if(opt$correct != "BH"){
  res$qvalue <- p.adjust(res$pvalue, method = opt$correct)
}


#DMC
dmc <- res[res$qvalue < opt$alpha, ]
dmc$pool1 <- ifelse(dmc$meth.diff > 0, "UP", "DOWN")


#save table
write.table(dmc, file = normalizePath(file.path(opt$out), 
                                      mustWork = FALSE), sep = "\t", 
            row.names = FALSE, quote = FALSE)




