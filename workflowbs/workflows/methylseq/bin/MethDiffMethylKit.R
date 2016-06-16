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

######### Analysis of DNA methylation data (with methylKit package) ############
################################################################################


### ---------------------Packages
#common packages
packages <- c("optparse", # to read arguments from a command line
              "ggplot2", # nice plots
              "reshape2",  # reshape grouped data
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
packagesBio <- c("rtracklayer", # read gff file
		 "GenomicRanges" # to use GRange object
)

for(package in packagesBio){
  # if package is installed locally, load
  if (!(package %in% rownames(installed.packages()))) {
    source("http://www.bioconductor.org/biocLite.R")
    biocLite(package)
  }
  do.call('library', list(package))
} 


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


sessionInfo()


### ---------------------Parameters

#############
###### Parameter initialization when the script is launched from command line
############
option_list = list(
  make_option(c("-d", "--directory"), type = "character", default = NULL, 
              help = "name of the directory where all files are stored 
              (files format: methylKit)", 
              metavar = "character"),
  make_option(c("-f", "--files"), type = "character", default = NULL, 
              help = "list of files path and name separated by ','
              (files format: methylKit)", 
              metavar = "character"),
  make_option(c("-R", "--reference"), type="character", default=NULL, 
              help="Reference genome name ", metavar="character"),
  make_option(c("-c", "--context"), type="character", default="CpG", 
              help="Methylation context [CpG,CHH,CHG,none]", metavar="character"),
  make_option(c("--destrand"), type="logical", default=TRUE, 
              help="if TRUE reads covering both strands of a CpG 
              dinucleotide will be merged [default=%default]", metavar="character"),
  make_option(c("--pool1"), type = "character", default = NULL,
              help = "library name in pool 1 separeted by ','", 
              metavar = "character"),
  make_option(c("--pool2"), type = "character", default = NULL,
              help = "library name in pool 2 separeted by ','", 
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
  make_option(c("-s", "--SNP"), type = "character", default = NULL, 
             help = "SNP file path and name (files format (without colnames): chr    pos)", 
             metavar = "character"),
  make_option(c("--gff"), type = "character", default = NULL,
              help = "annotation file (gff ot gtf files)", 
              metavar = "character"),
  make_option(c("--type"), type = "character", default = NULL,
              help = "list of interested type of regions separeted by ',' (e.g. 
              exon, intron, 5_prime_utr...)", 
              metavar = "character"),
  make_option(c("--tss"), type = "character", default = NULL,
              help = "file with TSS (files format (WITH colnames): chr    tss    strand)", 
              metavar = "character"),
  make_option(c("--parallel"), type = "logical", default = FALSE,
              help = "if TRUE some of the methods are performed on multiple core
              [default=%default]", 
              metavar = "character"),
  make_option(c("--ncores"), type = "integer", default = 1,
              help = "number of core in parallel mode", 
              metavar = "character"),
  make_option(c("--plots"), type = "logical", default = TRUE,
              help = "if TRUE plots are print
              [default=%default]", 
              metavar = "character"),
  make_option(c("-o", "--out"), type = "character", default = NULL, 
              help = "folder path where results are stored", 
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

#control on correction method
if (opt$plots & !is.null(opt$gff) & is.null(opt$type)){
  stop("type of feature (--type) are necessary when plots = TRUE and gff not NULL.")
}

#Create output folder if it didn't exist
ifelse(!dir.exists(opt$out), dir.create(opt$out), FALSE)

ifelse(!dir.exists(file.path(opt$out, "cleanData")), 
       dir.create(file.path(opt$out, "cleanData")), FALSE)

#Initialize parallel environment
if (opt$parallel){
  registerDoMC(opt$ncores)
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


#stop scrit if one pool name doesn't correspond to a filename
if (sum(!(pool1 %in% filenames)) != 0 |  sum(!(pool2 %in% filenames)) != 0){
  stop("A pool name doesn't match to filenames")
}

l <- l[filenames %in% c(pool1, pool2)]
filenames <- filenames[filenames %in% c(pool1, pool2)]

if(!is.null(opt$SNP)){
  snp <- read.table(opt$SNP) #Read SNP table without header
}

#keep only position covered on all samples and not SNP
files <- list()
keep <- NULL
for(i in seq_along(filenames)){
  files[[i]] <- read.table(l[i], header = TRUE)
  
  if (i == 1){
    keep <- files[[i]]$chrBase
  } else {
    keep <- intersect(keep, files[[i]]$chrBase)
  }
  
  #Remove SNP
  if(!is.null(opt$SNP)){
    keep <- keep[!is.element(keep, paste0(snp$V1,".",snp$V2))]
  }
}

for(i in seq_along(filenames)){
  write.table(files[[i]][files[[i]]$chrBase %in% keep, ], 
              file = normalizePath(file.path(opt$out, "cleanData", filenames[i]), 
                                   mustWork = FALSE), sep = "\t", 
              row.names = FALSE, quote = FALSE)
}
l <- normalizePath(file.path(opt$out, "cleanData", filenames), mustWork = FALSE)


#table with sample names and condition
sample_info <- data.frame(sample = filenames, 
                          condition = ifelse(filenames %in% pool1, 1, 2))
sample_info$sample <- as.character(sample_info$sample)
sample_info$name <- sapply(strsplit(sample_info$sample,"[.]"), head, n = 1)

#####################################################
### ---------------------------DMC with methylKit
#####################################################

#Input raw data
meth_data <- read(as.list(l), sample.id = as.list(filenames), 
                  assembly = opt$reference, context = opt$context,
                  treatment = ifelse(filenames %in% pool1, 1, 0))


#filter on high coverage
if (opt$filter){
  meth_data <- filterByCoverage(meth_data, hi.perc = 99)
  print("############### Filter on high coverage : DONE")
} else {
  print("############### No filter on high coverage")
}
meth_data_unite <- unite(meth_data)

#normalization
meth_data_norm <- meth_data
if (opt$normalization){
  meth_data_norm <- normalizeCoverage(meth_data_norm, method = "median")
  print("############### Median normalization : DONE")
} else {
  print("############### No normalization")
}

#filter
if (opt$filter){
  meth_data_norm <- filterByCoverage(meth_data_norm, lo.count = 5)
  print("############### Filter on low coverage : DONE")
} else {
  print("############### No filter on low coverage")
}


#only bases with coverage from all samples are retained andreads covering 
#both strands of a CpG dinucleotide are merged (if destrand=TRUE)
meth_data_norm_unite <- unite(meth_data_norm, destrand = opt$destrand)

#perform the test
res_test <- calculateDiffMeth(meth_data_norm_unite, slim = FALSE, weighted.mean = FALSE,
                              num.cores = opt$ncores)
res <- getData(res_test)

#change p-value correction if it's not "BH"
if (opt$correct != "BH"){
  res$qvalue <- p.adjust(res$pvalue, method = opt$correct)
}


#DMC
res_DMC <- res[res$qvalue < opt$alpha, ]
res_DMC$start <- res_DMC$start - 1
res_DMC$pool1 <- ifelse(res_DMC$meth.diff > 0, "UP", "DOWN")
#save DMC table
write.table(res_DMC, file = normalizePath(file.path(opt$out, "DMC.txt"), 
                                      mustWork = FALSE), sep = "\t", 
            row.names = FALSE, quote = FALSE)

print(paste0("############### Number of DMC : ", nrow(res_DMC)))

res_DMC_grange <- GRanges(seqnames = res_DMC$chr, ranges = IRanges(res_DMC$end, res_DMC$end),
                          strand = res_DMC$strand, name = res_DMC$pool1, score = res_DMC$meth.diff)

if(nrow(res_DMC) > 0){
  export(res_DMC_grange, normalizePath(file.path(opt$out, "DMC.bed"), mustWork = FALSE), 
       trackLine=new("BasicTrackLine", name = "DMC", 
                     description = paste0("pool1 (", paste(sample_info$name[sample_info$condition == 1], collapse = ", "),
                                          ") vs pool2 (", paste(sample_info$name[sample_info$condition == 2], collapse = ", "), ")"), 
                     useScore = TRUE))
}





#####################################################
### --------------------------------------------Plots
#####################################################
if(opt$plots){
  ######data
  
  ## dataframe with coverage per base
  #before low filter and normalization
  coverage_before_table <- getData(meth_data_unite)[,meth_data_unite@numCs.index] + 
    getData(meth_data_unite)[,meth_data_unite@numTs.index]
  coverage_before_table <- cbind(getData(meth_data_unite)[, 1:2], coverage_before_table)
  colnames(coverage_before_table) <- c("chr", "pos", meth_data_unite@sample.ids)
  
  
  coverage_before_table_long <- melt(coverage_before_table, id.vars = c("chr", "pos"))
  colnames(coverage_before_table_long)[3] <- "sample"
  coverage_before_table_long <- join_all(list(coverage_before_table_long, sample_info), 
                                      by = "sample")
  
  
  
  #after low filter and normalization
  coverage_after_table <- getData(meth_data_norm_unite)[,meth_data_norm_unite@numCs.index] + 
    getData(meth_data_norm_unite)[,meth_data_norm_unite@numTs.index]
  coverage_after_table <- cbind(getData(meth_data_norm_unite)[, 1:2], coverage_after_table)
  colnames(coverage_after_table) <- c("chr", "pos", meth_data_norm_unite@sample.ids)
  
  coverage_after_table_long <- melt(coverage_after_table, id.vars = c("chr", "pos"))
  colnames(coverage_after_table_long)[3] <- "sample"
  coverage_after_table_long <- join_all(list(coverage_after_table_long, sample_info), 
                                        by = "sample")
  
  
  ## dataframe with proportion of C per base
  #before low filter and normalization
  prop_before_table <- percMethylation(meth_data_unite)/100
  prop_before_table <- cbind(getData(meth_data_unite)[, 1:2], prop_before_table)
  colnames(prop_before_table) <- c("chr", "pos", meth_data_unite@sample.ids)
  
  
  #after low filter and normalization
  prop_after_table <- percMethylation(meth_data_norm_unite)/100
  prop_after_table <- cbind(getData(meth_data_norm_unite)[, 1:2], prop_after_table)
  colnames(prop_after_table) <- c("chr", "pos", meth_data_norm_unite@sample.ids)
  
  prop_after_table_long <- melt(prop_after_table, id.vars = c("chr", "pos"))
  colnames(prop_after_table_long)[3] <- "sample"
  prop_after_table_long <- join_all(list(prop_after_table_long, sample_info), 
                                    by = "sample")
  
  
  
  ## Plots functions
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
                         labels = sapply(strsplit(as.character(dendr$labels$label),"[.]"), head, n = 1)) + 
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
  
  
  
  ######plots
  pdf(file.path(opt$out, "images.pdf"), title = "Plots from methylKit",
      width = 12, height = 10)
  
  if (opt$normalization & opt$filter){
    title_after <- " after normalization and filtering"
  } else if (opt$normalization){
    title_after <- " after normalization"
  } else if (opt$filter) {
    title_after <- " after filtering"
  }
  
  #boxplots
  boxplotFunc(coverage_before_table[, -c(1,2)], "Read coverage distribution of methylated cytosines")
  boxplotFunc(coverage_after_table[, -c(1,2)], paste0("Read coverage distribution of methylated cytosines", 
                                                      title_after))
  
  
  #Density plots
  densityFunc(coverage_before_table_long, "Density plot on raw coverage")
  densityFunc(coverage_after_table_long, 
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
  
  
  
  ####
  
  #Distribution of the distance between 2 cytosines
  meth_data_norm_unite <- meth_data_norm_unite[order(meth_data_norm_unite$chr, 
                                                     meth_data_norm_unite$start), ]
  diff <- unlist(sapply(as.character(unique(meth_data_norm_unite$chr)), 
                        function(x) diff(meth_data_norm_unite$start[meth_data_norm_unite$chr == x[1]])))
  
  ggplot(data.frame(diff=diff), aes(x = log2(diff))) + 
    geom_density(adjust = 2) + ylab("Density") +
    theme_bw() + xlab(label = "Distance between 2 cytosines (log2)") + ggtitle("Distribution of the distance between 2 cytosines") 
  
  diffDMC <- NULL
  if(nrow(res_DMC) > 0){
    res_DMC <- res_DMC[order(res_DMC$chr, res_DMC$start), ]
    diffDMC <- unlist(sapply(as.character(unique(res_DMC$chr)), 
                             function(x) diff(res_DMC$start[res_DMC == x[1]])))
    
    ggplot(data.frame(diffDMC=diffDMC), aes(x = log2(diffDMC))) + 
      geom_density() + ylab("Density") +
      theme_bw() + xlab(label = "Distance between 2 DMC (log2)") + ggtitle("Distribution of the distance between 2 DMC") 
  }
  
  
  
  ####### annot
  dmc_type <- NULL
  prop_by_type <- NULL
  if(!is.null(opt$gff)){
    ## gff file
    gff <- import.gff3(opt$gff)
    
    #table with only chr-start-end-type from gff
    annot <- data.frame(chr = seqnames(gff), start = start(gff), end = end(gff), 
                        strand = strand(gff),
                        type = gff@elementMetadata@listData$type)
    
    #type of interest
    type <- unlist(strsplit(opt$type, ','))
    
    #annotation with only type of interest
    annot <- annot[annot$type %in% type, ] 
    
    ### Barplot
    if(nrow(res_DMC) > 0){
      dmc_grange <- GRanges(seqnames = res_DMC$chr,
                            IRanges(res_DMC$end, res_DMC$end),
                            strand = res_DMC$strand)
      
      dmc_type <- list()
      for(i in type){
        annot_grange <- GRanges(seqnames = annot$chr[annot$type == i],
                                IRanges(annot$start[annot$type == i],
                                        annot$end[annot$type == i]),
                                strand = annot$strand[annot$type == i])
        subset_type  <- suppressWarnings(subsetByOverlaps(dmc_grange, annot_grange))
        dmc_type[[i]] <- paste0(seqnames(subset_type), ".", start(subset_type))
      }
      dmc_type[["other"]] <- paste0(res_DMC$chr, ".", res_DMC$end)[!(paste0(res_DMC$chr, ".", res_DMC$end) %in% unlist(dmc_type))]
      dmc_type <- dmc_type[dmc_type != "."]
      
      ## plot
      number_type <- data.frame(type = as.factor(names(dmc_type)), frequency=sapply(dmc_type, length))
      number_type$type <-factor(number_type$type, levels=number_type$type[order(number_type$frequency, decreasing = TRUE)])
      
      p <- ggplot(number_type, aes(type, frequency)) + geom_bar(stat = "identity") +
        xlab("Type of region") + ylab("Frequency") + ggtitle("Number of DMC by type of region") +
        theme_bw()
      print(p)
      
      if (nrow(number_type) > 1){
        #Venn diagram
        plot.new()
        venn <- venn.diagram(
          x = dmc_type[names(dmc_type) != "other"],
          filename = NULL,
          cex = 1,
          fontface = "bold",
          cat.default.pos = "text",
          cat.cex = 1.5,
          cat.fontfamily = "serif",
          fontfamily = "serif",
          cat.dist = 0.06,
          cat.pos = 0,
          main = "Type of region for DMCs")
        grid.draw(venn)
      }
    }
    
    
    ### Boxplot
    cytosines_X_N <- GRanges(seqnames = as.character(getData(meth_data_norm_unite)[,1]), 
                             ranges = IRanges(as.numeric(getData(meth_data_norm_unite)[,2]), 
                                              as.numeric(getData(meth_data_norm_unite)[,3])),
                             X=getData(meth_data_norm_unite)[,meth_data_norm_unite@numCs.index],
                             N=getData(meth_data_norm_unite)[,meth_data_norm_unite@coverage.index])
    
    annotGrange <- GRanges(seqnames = annot$chr, IRanges(annot$start, annot$end))
    
    propTypeFunc <- function(x){
      temp <- GRanges(seqnames = x$chr[1], IRanges(x$start[1], x$end[1]))
      
      overlaps <- suppressWarnings(subsetByOverlaps(cytosines_X_N, temp))
      
      if(length(overlaps) > 0){
        prop1 <- sum(as.data.frame(elementMetadata(overlaps)[, 1:nrow(sample_info)])[, sample_info$sample %in%pool1]) / 
          sum(as.data.frame(elementMetadata(overlaps)[, (nrow(sample_info)+1):(2*nrow(sample_info))])[, sample_info$sample %in%pool1])
        
        prop2 <- sum(as.data.frame(elementMetadata(overlaps)[, 1:nrow(sample_info)])[, sample_info$sample %in%pool2]) / 
          sum(as.data.frame(elementMetadata(overlaps)[, (nrow(sample_info)+1):(2*nrow(sample_info))])[, sample_info$sample %in%pool2])
        
        return(data.frame(proportion = c(prop1, prop2), condition = c(1,2), type = rep(x$type[1], 2)))
      }
    }
    
    overlaps_total <- suppressWarnings(findOverlaps(cytosines_X_N, annotGrange))
    
    if(length(subjectHits(overlaps_total)) > 0){
      notempty <- unique(as.numeric(subjectHits(overlaps_total)))
      prop_by_type <- adply(annot[notempty,], 1, propTypeFunc, .parallel = opt$parallel)
      
      
      #boxplot
      my_stats <- function(x) {
        res <- quantile(as.numeric(as.character(prop_by_type$proportion[as.numeric(prop_by_type$condition) == x[[1]] & 
                                                                          as.character(prop_by_type$type) == x[[2]]])), 
                        probs = c(0, 0.25, 0.5, 0.75, 1))
        names(res) <- c("ymin", "lower", "middle", "upper", "ymax")
        return(res)
      }
      
      df <- apply(unique(data.frame(prop_by_type$condition, as.character(prop_by_type$type))), 1, my_stats)
      df <- data.frame(unique(data.frame(prop_by_type$condition, as.character(prop_by_type$type))), t(df))
      colnames(df)[1:2] <- c("condition", "type")
      p <- ggplot(df, aes(x = as.factor(condition), ymin = ymin, ymax = ymax, lower = lower,
                          upper = upper, middle = middle, fill = as.factor(condition))) +
        theme_bw() + geom_boxplot(stat = "identity") + facet_grid(.~type) +
        scale_fill_manual(name = "Conditions", values = c("steelblue3", "springgreen3")) +
        ylab("Proportion of methylation") + ggtitle("Boxplot on proportion of methylation 
  by type of region and condition") + xlab("Conditions")
      print(p)
      
    }
    
  }
  
  
  ######## TSS
  dist_to_tss_long <- NULL
  if(!is.null(opt$tss)){
    prop_after_grange <- GRanges(seqnames = as.character(getData(meth_data_norm_unite)[,1]), 
                                 ranges = IRanges(as.numeric(getData(meth_data_norm_unite)[,2]), 
                                                  as.numeric(getData(meth_data_norm_unite)[,3])),
                                 prop=percMethylation(meth_data_norm_unite)/100)
    
    
    tss <- read.table(opt$tss, header = TRUE)
    tssGrange <- GRanges(seqnames = tss$chr, IRanges(tss$tss - 5000, tss$tss + 5000))
    
    tssFunc <- function(x){
      temp <- GRanges(seqnames = x$chr[1], IRanges(x$tss[1] - 5000, x$tss[1] + 5000))
      overlaps <- suppressWarnings(subsetByOverlaps(prop_after_grange, temp))
      
      res <- NULL
      if(length(overlaps) > 0){
        for(j in 1:length(overlaps)){
          
          dist <- ifelse(as.character(x$strand[1]) == "+", start(overlaps)[j] - as.numeric(x["tss"]), 
                         as.numeric(x["tss"]) - start(overlaps)[j])
          prop <- as.data.frame(elementMetadata(overlaps))[j, ]
          
          res <- rbind(res, data.frame(distance = dist, prop))
          
        }
      }
      
      return(res)
    }
    
    overlaps_total <- suppressWarnings(findOverlaps(prop_after_grange, tssGrange))
    
    if(length(subjectHits(overlaps_total)) > 0){
      notempty <- unique(as.numeric(subjectHits(overlaps_total)))
      dist_to_tss <- adply(tss[notempty,], 1, tssFunc, .parallel = opt$parallel)
      
      
      
      dist_to_tss <- dist_to_tss[, -c(1:3)]
      
      dist_to_tss_long <- melt(dist_to_tss, id.vars = c("distance"))
      dist_to_tss_long$variable <- sapply(strsplit(as.character(dist_to_tss_long$variable), "[.]"), "[[", 2)
      ggplot(dist_to_tss_long, 
             aes(x = distance, y = value, colour = variable)) +
        geom_smooth(method="gam", formula = y ~ s(x, k = 50, bs = "cs"), se = FALSE) + 
        ylim(c(0,1)) + theme_bw() + guides(color=guide_legend(title="Samples")) +
        xlab("Distance to TSS") + ylab("Smooth proportion of methylation") +
        ggtitle("Smooth proportion of methylation by distance to TSS")
    }
    
  }
  
  
  dev.off()
  
  save(coverage_before_table, coverage_after_table,
       coverage_before_table_long, coverage_after_table_long,
       prop_after_table_long, prop_before_table, prop_after_table,
       diff, diffDMC,
       dmc_type, prop_by_type, dist_to_tss_long,
       sample_info,
       file = normalizePath(file.path(opt$out, 
                                      "data_for_graph.Rdata"), 
                            mustWork = FALSE))
}
