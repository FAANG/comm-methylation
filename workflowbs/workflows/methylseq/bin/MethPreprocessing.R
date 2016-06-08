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

################## Preprocessing of DNA methylation data #######################
################################################################################


### ---------------------Packages
#common packages
packages <- c("optparse", # to read arguments from a command line
              "ggplot2", # nice plots
              "reshape2",  # reshape grouped data
              "ggdendro", # to plot dendrogram,
              "plyr", #tools for Splitting, Applying and Combining Data
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
packages_bio <- c("edgeR" # RLE normalization
)

for(package in packages_bio){
  # if package is installed locally, load
  if (!(package %in% rownames(installed.packages()))) {
    source("http://www.bioconductor.org/biocLite.R")
    biocLite(package)
  }
  do.call('library', list(package))
} 


### ---------------------Parameters

#############
###### Parameter initialization when the script is launched from command line
############
option_list = list(
  make_option(c("-d", "--directory"), type = "character", default = NULL, 
              help = "name of the directory where all files are stored (files format 
              chr    pos    N    X)", metavar = "character"),
  make_option(c("-f", "--files"), type = "character", default = NULL, 
              help = "list of files path and name separated by ',' (files format 
              chr    pos    N    X)", metavar = "character"),
  make_option(c("--format"), type = "character", default = "dss", 
              help = "file format (dss, methylkit or bismark)  [default=%default]", 
              metavar = "character"),
  make_option(c("-m", "--method"), type = "character", default = "libsize", 
              help = "normalization method ('libsize', 'median', 'UP', 'RLE', 'LR'
              or 'none') [default=%default]", 
              metavar = "character"),
  make_option(c("-s", "--SNP"), type = "character", default = NULL, 
              help = "SNP file path and name (files format 
              chr    pos)", 
              metavar = "character"),
  make_option(c("--highCoverage"), type = "integer", default = NULL, 
              help = "Bases having higher coverage than this count are removed", 
              metavar = "character"),
  make_option(c("--lowCoverage"), type = "integer", default = FALSE, 
              help = "Bases having lower coverage than this count are removed 
               [default=%default]"), 
  make_option(c("--pool1"), type = "character", default = NULL,
              help = "files name in pool 1 separeted by ','", 
              metavar = "character"),
  make_option(c("--pool2"), type = "character", default = NULL,
              help = "files name in pool 2 separeted by ','", 
              metavar = "character"),
  make_option(c("--parallel"), type = "logical", default = FALSE,
              help = "if TRUE some of the methods are performed on multiple cores
              [default=%default]", 
              metavar = "character"),
  make_option(c("--ncores"), type = "integer", default = NULL,
              help = "number of cores in parallel mode", 
              metavar = "character"),
  make_option(c("--plots"), type = "logical", default = TRUE,
              help = "if TRUE plots are print
              [default=%default]", 
              metavar = "character"),
  make_option(c("-o", "--out"), type = "character", default = NULL, 
              help = "folder path where results are stored", 
              metavar = "character")
  )

opt_parser = OptionParser(usage="Imports data and does one normalization methods.", 
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
  stop("pools are necessary for low coverage filter and plots.\n", call. = FALSE)
}

#control on normalization method
if (!(opt$method %in% c("libsize", "median", "UP", "RLE", "LR", "none"))){
  stop("This normalization method doesn't exist.")
}

#control on file's format
if (!(opt$format %in% c("dss", "methylkit", "bismark"))){
  stop("This file format doesn't exist.")
}

#Create output folder if it didn't exist
ifelse(!dir.exists(opt$out), dir.create(opt$out), FALSE)

#Initialize parallel environment
if (opt$parallel){
  registerDoMC(opt$ncores)
}


#####################################################
### ---------------------Input data and preprocessing
#####################################################
#Input raw count
files <- list()
strand <- NULL
names <- character() #vector of filenames (useful for saving the 
#normalized data)

#vector of path and filenames
if (!is.null(opt$directory)){
  l <- dir(opt$directory)
  l <- l[regexpr(pattern = ".txt", l, fixed = TRUE) != -1]
  names <- l
  l <- normalizePath(file.path(opt$directory, l), mustWork = FALSE)
} else {
  l <- unlist(strsplit(opt$files, ','))
  names <- sapply(strsplit(l, '/'),tail, n=1)
}

#pool: compare list in opt$pool1 and opt$pool2 with names
pool1 <- unlist(strsplit(opt$pool1, ','))
pool2 <- unlist(strsplit(opt$pool2, ','))


#stop scrit if one pool name doesn't correspond to a filename
if (sum(!(pool1 %in% names)) != 0 |  sum(!(pool2 %in% names)) != 0){
  stop("A pool name doesn't match to filenames")
}

l <- l[names %in% c(pool1, pool2)]
names <- names[names %in% c(pool1, pool2)]

#read SNP table
if(!is.null(opt$SNP)){
  snp <- read.table(opt$SNP, header=TRUE) #Read SNP table
}

#read all files
for (i in seq_along(l)){
  read_header = TRUE
  if (opt$format == "bismark") {
    read_header = FALSE
  }
  files[[i]] <- read.table(l[i], header = read_header)
  
  
  #control on file's format
  if (opt$format == "methylkit"){
    if (sum(colnames(files[[i]]) %in% c("chr", "base", "strand", "coverage",
                                       "freqC")) != 5) {
      stop("Columns names does not correspond to methylkit format (chr, 
      base, coverage, freqC and strand).")
    } else {
      files[[i]] <- data.frame(chr = files[[i]]$chr,
                               pos = files[[i]]$base,
                               strand = files[[i]]$strand,
                               N = files[[i]]$coverage,
                               X = round(files[[i]]$freqC * files[[i]]$coverage / 100))
    }
    
  } else if (opt$format == "bismark") {
    if (length(colnames(files[[i]])) != 7 || files[[i]]$V1[1] != "chrBase" 
    || files[[i]]$V1[1] != "chr") {
      stop("Unexpected file format for bismark, must have 7 columns 
      without header (CX_report file).")
    } else {
      files[[i]] <- data.frame(chr = files[[i]]$V1,
                               pos = files[[i]]$V2,
                               strand = files[[i]]$V3,
                               N = files[[i]]$V4 + 
                                 files[[i]]$V5,
                               X = files[[i]]$V4)
    }
    
  } else {
    if (sum(colnames(files[[i]]) %in% c("chr", "pos", "strand", "N",
                                       "X")) != 5) {
      stop("Columns names not correspond to dss format (chr, pos, N, X 
      and strand) please use --format option to specify format.")
    }
  }
  
  
  files[[i]]$strand <- ifelse(files[[i]]$strand == "F", "+", "-")
  strand <- rbind(strand, files[[i]][, c("chr", "pos", "strand")])
  strand <- unique(strand)
  
  files[[i]] <- files[[i]][, c("chr", "pos", "N", "X")]
  
  #Remove position with a high coverage
  if(!is.null(opt$highCoverage)){
    files[[i]] <- files[[i]][files[[i]]$N < opt$highCoverage,]
    print("############### Filter on high coverage : DONE")
  } else {
    print("############### No filter on high coverage")
  }
  
  #Remove SNP
  if(!is.null(opt$SNP)){
    files[[i]] <- files[[i]][!is.element(paste0(files[[i]]$chr,"_",files[[i]]$pos),
                                         paste0(snp$chr,"_",snp$pos)),]
    print("############### Remove SNP : DONE")
  }
}

#table with sample names and condition
sample_info <- data.frame(sample=c(pool1, pool2), 
                          condition=c(rep(1,length(pool1)),
                                      rep(2, length(pool2))))
sample_info$sample <- as.character(sample_info$sample)

#obtain the same order between pool and list of count datasets
files <- files[match(sample_info$sample, names)]


#####################################################
### ------------------------Normalization on coverage
#####################################################
#Keep only the coverage (N) to perform the normalization
files_for_norm_func <- function(x){
  res <- files[[x]][, c("chr", "pos", "N")]
  colnames(res)[3] <- sample_info$sample[x]
  return(res)
}

files_for_norm <- llply(seq_along(files), files_for_norm_func, .parallel = opt$parallel)


#Merge all dataframes
counts <- join_all(files_for_norm, by= c("chr", "pos"), type = "full")
counts <- counts[rowSums(is.na(counts))==0 , ]
rownames(counts) <- paste0(counts[, 1], ".", counts[, 2])
counts <- counts[, 3:ncol(counts)]


########---------------------Normalization functions

## Normalization by library size
libsize_norm <- function(counts){
  #the sequencing depth is obtained with
  library_size <- colSums(counts)
  
  #and, using the first sample for the reference, the normalization coefficients
  #are obtained by:
  s_values <- library_size / max(library_size)
  return(s_values)
}


## Normalization by median or third quartile
quantile_norm <- function(counts, probs){
  #the median or the third quaartile is obtained with
  count_quantile <- apply(counts, 2, quantile, probs = probs)
  
  #and, using the first sample as the reference sample, the normalization 
  #coefficients are obtained by:
  s_values <- count_quantile / count_quantile[which.max(colSums(counts))]
  return(s_values)
}

## Normalization by RLE method
RLE_norm <- function(counts){
  # create a DGE object
  dge <- DGEList(counts = counts, remove.zeros = TRUE)
  
  # compute normalization factors
  dge <- calcNormFactors(dge, method = "RLE")
  
  # and normalization factors
  norm_factor <- dge$samples$norm.factors
  return(norm_factor)
}


## Normalization by LR method
LR_norm <- function(counts){
  # adapted from DSS package
  ix <- which.max(colSums(counts))## use this one as basis
  X0 <- counts[,ix]
  norm_factor <- rep(1, ncol(counts))
  
  for(i in 1:ncol(counts)) {
    ii <- X0>0 & counts[,i]>0
    lr <- log(X0[ii] / counts[ii,i])
    ## trim 5%
    qq <- quantile(lr, c(0.05, 0.95))
    lr2 <- lr[lr>qq[1] & lr<qq[2]]
    norm_factor[i] <- exp(-median(lr2))
  }
  
  norm_factor[ix] <- 1
  return(norm_factor)
}
########--------------------------------------------

# compute normalization 
norm_factor <- NULL
if (opt$method == "libsize"){
  norm_factor <- libsize_norm(counts)
  print("############### Libsize normalization : DONE")
} else if (opt$method == "median"){
  norm_factor <- quantile_norm(counts, 0.5)
  print("############### Median normalization : DONE")
} else if (opt$method == "UP"){
  norm_factor <- quantile_norm(counts, 0.75)
  print("############### Upper-quantile normalization : DONE")
} else if (opt$method == "RLE"){
  norm_factor <- RLE_norm(counts)
  print("############### RLE normalization : DONE")
} else if (opt$method == "LR"){
  norm_factor <- LR_norm(counts)
  print("############### LR normalization : DONE")
} else if (opt$method == "none"){
  print("############### No normalization")
} else {
  stop("This normalization method doesn't exist.")
}


if(opt$method == "RLE"){
  max_libsize <- max(colSums(counts))
  norm_counts <- round(sweep(counts * max_libsize, 2,
                             colSums(counts) * norm_factor, "/"))
} else if(opt$method == "none") {
  norm_counts <- counts
} else {
  norm_counts <- round(sweep(counts, 2, norm_factor, "/"))
}

#filter on low coverage


if (!is.null(opt$lowCoverage)){
  is_not_filtering <- rowSums(norm_counts > opt$lowCoverage) == length(names) 
  list_not_filtering <- names(is_not_filtering)[is_not_filtering]
  print("############### Filter on low coverage : DONE")
} else {
  is_not_filtering <- rep(TRUE, nrow(norm_counts))
  list_not_filtering <- rownames(norm_counts)
  print("############### No filter on low coverage")
}

#save clean methylation data (filter on coverage and normalization)
files_norm <- list()
for(i in seq_along(files)){
  #position to save
  position <- paste0(files[[i]]$chr, ".", files[[i]]$pos)
  pos_to_save <- position %in% list_not_filtering
  
  #files to save
  if(opt$method == "RLE"){
    norm_count_toSave <- norm_counts[is_not_filtering,]
    
    toSave <- files[[i]][pos_to_save, ]
    toSave <- toSave[match(rownames(norm_count_toSave),
                           paste0(toSave$chr, ".", toSave$pos)), ]
    
    p <- toSave[, "X"] / toSave[, "N"]
    Xnorm <- round(p * norm_count_toSave[, i])
    files_norm[[i]] <- data.frame(toSave[, c("chr", "pos")], 
                                  N=norm_count_toSave[, i],
                                  X=Xnorm)
  } else if(opt$method == "none") {
    files_norm[[i]] <- data.frame(files[[i]][pos_to_save, c("chr", "pos")], 
                                  files[[i]][pos_to_save, c("N", "X")])
  } else {
    files_norm[[i]] <- data.frame(files[[i]][pos_to_save, c("chr", "pos")], 
                                  round(files[[i]][pos_to_save, c("N", "X")]/norm_factor[i]))
  }
  
  files_norm[[i]] <- join_all(list(files_norm[[i]], strand), by= c("chr", "pos"))
  
  write.table(files_norm[[i]], file = normalizePath(file.path(opt$out, 
                                                              sample_info$sample[i]), 
                                                    mustWork = FALSE), sep = "\t", 
              row.names = FALSE, quote = FALSE)
}








#####################################################
### --------------------------------------------Plots
#####################################################
if(opt$plots){
  
  ### function
  #Boxplot on coverage
  my_stats <- function(x) {
    res <- quantile(x, probs = c(0, 0.25, 0.5, 0.75, 1))
    names(res) <- c("ymin", "lower", "middle", "upper", "ymax")
    return(res)
  }
  
  boxplotFunc <- function(counts, tit){
    res <- as.data.frame(t(apply(counts, 2, my_stats)))
    df <- data.frame(sample = sapply(strsplit(sample_info$sample,"[.]"), head, n = 1), res, 
                     condition = as.factor(ifelse(sample_info$sample %in% pool1, 1, 2)))
    p <- ggplot(df, aes(x = sample, ymin = ymin, ymax = ymax, lower = lower,
                        upper = upper, middle = middle, fill = condition)) +
      theme_bw() +
      theme(axis.text.x = element_text(angle = 70, vjust = 1, hjust=1, colour = "black")) +
      scale_fill_manual(name = "Conditions", values = c("steelblue3", "springgreen3")) +
      geom_boxplot(stat = "identity") + ggtitle(tit) 
    print(p)
  }
  
  
  #Density plot on coverage
  densityFunc <- function(dat, tit) {
    p <- ggplot(dat, aes(x = value, group = sample)) + 
      geom_density(aes(colour = factor(condition)), adjust = 7) + 
      theme_bw() + xlab(label = "coverage") + ggtitle(tit) + 
      guides(color=guide_legend(title="Conditions")) + 
      scale_color_manual(name = "Conditions", 
                         values = c("steelblue3", "springgreen3"))
    print(p)
  }
  
  densityFuncProp <- function(dat, tit) {
    p <- ggplot(dat, aes(x = value, group = sample)) + 
      geom_density(aes(colour = factor(condition)), adjust = 5) + 
      theme_bw() + xlab(label = "proportion") + ggtitle(tit) + 
      guides(color=guide_legend(title="Conditions")) + 
      scale_color_manual(name = "Conditions", 
                         values = c("steelblue3", "springgreen3"))
    print(p)
  }
  
  densityFunc20 <- function(counts, tit){
    top20 <- names(sort(table(counts$chr), 
                        decreasing = TRUE)[1:(min(20, length(table(counts$chr))))])
    
    p <- ggplot(counts[counts$chr %in% top20 ,], 
                aes(x = value, group = sample)) + 
      geom_density(aes(colour = factor(condition))) + 
      facet_wrap(~chr) +
      theme_bw() + xlab(label = "coverage") + 
      ggtitle(tit) + 
      guides(color=guide_legend(title="Conditions")) + 
      scale_color_manual(name = "Conditions", 
                         values = c("steelblue3", "springgreen3"))
    
    print(p)
    
  }
  
  ##Dendrogram
  dendrogramFunc <- function(dat, tit){
    dendr <- dendro_data(hclust(dist(t(dat))), 
                         type="rectangle") 
    dendr$segments <- merge(dendr$segments, dendr$labels, 
                            by = "x", all.x = TRUE)
    dendr$segments$condition <- as.factor(ifelse(dendr$segments$label %in% pool1, 
                                                 1, 2))
    
    p <- ggplot() + 
      geom_segment(data=segment(dendr), aes(x=x, y=y.x, xend=xend, yend=yend, 
                                            colour = condition)) +
      geom_segment(data=segment(dendr), aes(x=x, y=y.x, xend=xend, yend=yend), 
                   size = 1) +
      scale_x_continuous(breaks = seq_along(sample_info$sample), 
                         labels = sapply(strsplit(sample_info$sample,"[.]"), head, n = 1)) + 
      ylab("Distance") +
      theme(axis.line.x=element_blank(),
            axis.ticks.x=element_blank(),
            axis.title.x=element_blank(),
            panel.background=element_rect(fill="white"),
            panel.grid=element_blank(),
            panel.grid.minor.x=element_blank(),
            axis.text.x = element_text(angle = 90, vjust = 1, size=10, hjust=1, 
                                       colour = ifelse(dendr$labels$label %in% pool1, 
                                                       "steelblue4", "springgreen4"))) +
      scale_colour_manual(name = c("Conditions"), values = c("steelblue4", "springgreen4")) +
      ggtitle(tit)
    print(p)
  }
  
  
  #PCA
  pcaFunc <- function(dat, tit) {
    pca <- data.frame(prcomp(dat)$rotation)
    pca$name <- rownames(pca)
    pca$label <- sapply(strsplit(rownames(pca),"[.]"), head, n = 1)
    p <- ggplot(pca, aes(x = PC1, y = PC2, label = label, 
                         color = as.factor(ifelse(pca$name %in% pool1, 1, 2)))) + 
      geom_point(size=4) + geom_text(hjust=0.5, vjust=-1) + theme_bw() + 
      xlab(label = "Dimension 1") + ylab(label = "Dimension 2") + 
      ggtitle(tit) + scale_color_manual(name = "Conditions", 
                                        values = c("steelblue3", "springgreen3")) +
      xlim(min(pca$PC1) - (max(pca$PC1) - min(pca$PC1))/4, 
           max(pca$PC1) + (max(pca$PC1) - min(pca$PC1))/4)
    print(p)
  }
  
  
  ##Correlation
  cmd.args <- commandArgs()
  m <- regexpr("(?<=^--file=).+", cmd.args, perl=TRUE)
  path_ezcor <- file.path(dirname(regmatches(cmd.args, m)),"ezCor.R")
  source(path_ezcor)
  
  
  
  
  ####Data
  
  ## dataframe with coverage per base
  #before low filter and normalization
  counts_long <- melt(counts)
  colnames(counts_long)[1] <- "sample"
  counts_long <- join_all(list(counts_long, sample_info), by= "sample")
  
  #after low filter and normalization
  norm_counts_long <- melt(norm_counts[is_not_filtering, ])
  colnames(norm_counts_long)[1] <- "sample"
  norm_counts_long <- join_all(list(norm_counts_long, sample_info), by= "sample")
  
  
  ## dataframe with proportion of C per base
  #before low filter and normalization
  prop_before_func <- function(x){
    res <- data.frame(chr = files[[x]]$chr, pos = files[[x]]$pos,
                      prop = files[[x]]$X / files[[x]]$N)
    colnames(res)[3] <- sample_info$sample[x]
    return(res)
  }
  prop_before <- llply(seq_along(files), prop_before_func, .parallel = opt$parallel)
  
  prop_before_table <- join_all(prop_before, type = "full")
  prop_before <- NULL
  prop_before_table <- prop_before_table[rowSums(is.na(prop_before_table))==0 , ]
  
  
  #after low filter and normalization
  prop_after_func <- function(x){
    res <- data.frame(chr = files_norm[[x]]$chr, pos = files_norm[[x]]$pos,
                      prop = files_norm[[x]]$X / files_norm[[x]]$N)
    colnames(res)[3] <- sample_info$sample[x]
    return(res)
  }
  prop_after <- llply(seq_along(files_norm), prop_after_func, .parallel = opt$parallel)
  prop_after_table <- join_all(prop_after, type = "full")
  prop_after <- NULL
  prop_after_table <- prop_after_table[rowSums(is.na(prop_after_table))==0 , ]
  prop_after_table_long <- melt(prop_after_table, id.vars = c("chr", "pos"))
  colnames(prop_after_table_long)[3] <- "sample"
  prop_after_table_long <- join_all(list(prop_after_table_long, sample_info), 
                                    by = "sample")
  
  
  
  ####Plots
  pdf(file.path(opt$out, "images_normalization.pdf"), title = "Plots from DSS (normalization)",
      width = 12, height = 10)
  
  
  if (!is.null(opt$method) & !is.null(opt$lowCoverage) & !is.null(opt$highCoverage)){
    title_after <- " after normalization and filtering"
  } else if (!is.null(opt$method) & !is.null(opt$lowCoverage)){
    title_after <- " after normalization and low filtering"
  } else if (!is.null(opt$method) & !is.null(opt$highCoverage)){
    title_after <- " after normalization and high filtering"
  } else if (!is.null(opt$highCoverage) & !is.null(opt$lowCoverage)){
    title_after <- " after filtering"
  } else if (!is.null(opt$method)) {
    title_after <- " after normalization"
  } else if (!is.null(opt$lowCoverage)) {
    title_after <- " after low filtering"
  } else if (!is.null(opt$highCoverage)) {
    title_after <- " after high filtering"
  }
  
  
  #boxplots
  boxplotFunc(counts, "Read coverage distribution of methylated cytosines")
  boxplotFunc(norm_counts[is_not_filtering, ], paste0("Read coverage distribution of methylated cytosines", 
                                                      title_after))
  
  
  #Density plots
  densityFunc(counts_long, "Density plot on raw coverage")
  densityFunc(norm_counts_long, 
              paste0("Density on coverage", 
                     title_after))
  
  #Density plot on proportion for all chromosomes
  densityFuncProp(prop_after_table_long, 
                  paste0("Density on methylation proportion", title_after))
  #Density plot on proportion for the 20 chromosomes with the most covered cytosines
  densityFunc20(prop_after_table_long, paste0("Density on methylation proportion", 
                                              title_after, " for 
            the 20 chromosomes with the highest number of covered cytosines"))
  
  
  #Dendrogram et PCA only if there is more than 2 samples
  if(length(pool1) != 1 & length(pool2) != 1) {
    #Dendrogram
    dendrogramFunc(prop_before_table[, -c(1,2)], "Dendrogram on raw proportion")
    dendrogramFunc(prop_after_table[, -c(1,2)], 
                   paste0("Dendrogram on proportion", 
                          title_after))
    
    #PCA
    pcaFunc(prop_before_table[, -c(1,2)], "PCA plot on raw proportion")
    pcaFunc(prop_after_table[, -c(1,2)], 
            paste0("PCA plot on proportion", 
                   title_after))
  }
  
  
  #Correlation plot
  ezCor(prop_before_table[, -c(1,2)], pool1, "Correlation on raw proportion") 
  ezCor(prop_after_table[, -c(1,2)], pool1, 
        paste0("Correlation on proportion", 
               title_after))
  
  dev.off()
  
  save(counts, norm_counts, is_not_filtering, counts_long, norm_counts_long,
       prop_after_table_long, prop_before_table, prop_after_table,
       file = normalizePath(file.path(opt$out, 
                                      "data_for_graph.Rdata"), 
                            mustWork = FALSE))
}







