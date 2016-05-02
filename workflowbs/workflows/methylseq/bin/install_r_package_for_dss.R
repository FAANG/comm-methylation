
### ---------------------Packages
packages <- c("optparse",# to read arguments from a command line
              "ggplot2", # nice plots
              "reshape2",  # reshape grouped data
              "ggdendro", # to plot dendrogram,
              "plyr", # tools for Splitting, Applying and Combining Data
              "dplyr", # tools for Splitting, Applying and Combining Data
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
packagesBio <- c("DSS",# for beta-binomial model
              "rtracklayer", # read gff file
              "edgeR" # RLE normalization
)

for(package in packagesBio){
  # if package is installed locally, load
  if (!(package %in% rownames(installed.packages()))) {
    source("http://www.bioconductor.org/biocLite.R")
    biocLite(package)
  }
  do.call('library', list(package))
} 
