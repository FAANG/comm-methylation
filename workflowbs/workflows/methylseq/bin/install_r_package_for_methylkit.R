#common packages
packages <- c("optparse", # to read arguments from a command line
              "GenomicRanges", # to use GRange object
              "ggplot2", # nice plots
              "reshape2",  # reshape grouped data
             "edmr", # to find DMR
             "ggdendro", # to plot dendrogram,
             "plyr", # for matrix plots
             "VennDiagram", # for Venn diagram
             "doMC", # for parallel environment
             "grid") #for layout in plots 

for(package in packages){
  # if package is installed locally, load
  if (!(package %in% rownames(installed.packages()))) {
    install.packages(package, repos="http://cran.univ-paris1.fr")
  }
  do.call('library', list(package))
}  

#Bioconductor package
#read a gff file
if (!("rtracklayer" %in% rownames(installed.packages()))) {
  source("http://www.bioconductor.org/biocLite.R")
  biocLite("rtracklayer")
}
library(rtracklayer) 


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