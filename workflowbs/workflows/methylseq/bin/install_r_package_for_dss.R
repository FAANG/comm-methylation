#
# Copyright (C) 2016 INRA
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

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
