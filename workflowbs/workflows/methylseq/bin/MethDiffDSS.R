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

##################### Analysis of DNA methylation data #########################
################################################################################


### ---------------------Packages
packages <- c("optparse",# to read arguments from a command line
              "ggplot2", # nice plots
              "reshape2",  # reshape grouped data
              "plyr", # tools for Splitting, Applying and Combining Data
              "dplyr", # tools for Splitting, Applying and Combining Data
              "VennDiagram", # for Venn diagram
              "doMC" # for parallel environment
)

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
              "edgeR", # RLE normalization
              "ChIPpeakAnno" # correspondance gene-DMR
)


for(package in packagesBio){
  # if package is installed locally, load
  if (!(package %in% rownames(installed.packages()))) {
    source("http://www.bioconductor.org/biocLite.R")
    biocLite(package)
  }
  do.call('library', list(package))
} 

sessionInfo()
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
  make_option(c("--pool1"), type = "character", default = NULL,
              help = "library name in pool 1 separeted by ','", 
              metavar = "character"),
  make_option(c("--pool2"), type = "character", default = NULL,
              help = "library name in pool 2 separeted by ','", 
              metavar = "character"),
  make_option(c("--alpha"), type = "double", default = 0.05,
              help = "significance level of the tests (i.e. acceptable rate of 
              false-positive in the list of DMC) 
              [default=%default]", 
              metavar = "character"),
  make_option(c("--correct"), type = "character", default = "BH",
              help = "method used to adjust p-values for multiple testing 
              ('BH' or 'bonferroni') [default=%default]", metavar = "character"),
  make_option(c("--dmr"), type = "logical", default = FALSE,
              help = "if TRUE DMR are extract [default=%default]", 
              metavar = "character"),
  make_option(c("--dmr.numC"), type = "double", default = 3,
              help = "cutoff of the number of CpGs (CHH or CHG) in each region to 
              call DMR [default=%default]", 
              metavar = "character"),
  make_option(c("--dmr.propDMC"), type = "double", default = 1,
              help = "cutoff of the proportion of DMCs in each region to call DMR 
              [default=%default]", 
              metavar = "character"),
  make_option(c("--dmr.type"), type = "character", default = "qvalue",
              help = "definition of DMC in DMR ('pvalue' or 'qvalue') 
              [default=%default]", 
              metavar = "character"),
  make_option(c("--gff"), type = "character", default = NULL,
              help = "annotation file (gff ot gtf files)", 
              metavar = "character"),
  make_option(c("--type"), type = "character", default = NULL,
              help = "list of interested type of regions separeted by ',' (e.g. 
              exon, intron, 5_prime_utr...)", 
              metavar = "character"),
  make_option(c("--tss"), type = "character", default = NULL,
              help = "file with TSS (files format: chr    tss    strand)", 
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
if (!(opt$correct %in% c("BH", "bonferroni"))){
  stop("This normalization method doesn't exist.")
}

#control on correction method
if (opt$plots & !is.null(opt$gff) & is.null(opt$type)){
  stop("type of feature (--type) are necessary when plots = TRUE and gff not NULL.")
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

#Input normalize data
files <- list()
strand <- NULL

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

#read all files
for (i in seq_along(l)){
  files[[i]] <- read.table(l[i], header = TRUE)
  strand <- files[[i]][, c("chr", "pos", "strand")]
  
  
  files[[i]] <- files[[i]][, c("chr", "pos", "N", "X")]
}


#table with sample names and condition
sample_info <- data.frame(sample=c(pool1, pool2), 
                          condition=c(rep(1,length(pool1)),
                                      rep(2, length(pool2))))
sample_info$sample <- as.character(sample_info$sample)
sample_info$name <- sapply(strsplit(sample_info$sample,"[.]"), head, n = 1)

#obtain the same order between pool and list of count datasets
files <- files[match(sample_info$sample, names)]



#####################################################
### -------------------------------------DMC with DSS
#####################################################
#create a BSseq object
BSobj <- makeBSseqData(files, sample_info$sample)

#perform the test
if(length(pool1) > 1 & length(pool2) > 1){ # at least TWO replicats by conditions
  dmlTest <- DMLtest(BSobj, group1 = pool1, group2 = pool2)
} else {
  dmlTest <- DMLtest(BSobj, group1 = pool1, group2 = pool2, smoothing = TRUE)
}


## DMC
res_DMC <- dmlTest

#adjust p-value
res_DMC$padj <- p.adjust(res_DMC$pval, method = opt$correct)
dmlTest$padj <- p.adjust(dmlTest$pval, method = opt$correct)

#Table of p-value: only cytosines with an adjusted p-value < opt$alpha
res_DMC <- res_DMC[res_DMC$padj < opt$alpha, ]

#BED format
res_DMC$start <- res_DMC$pos - 1
res_DMC$end <- res_DMC$pos
res_DMC$pos <- NULL
res_DMC$pool1 <- ifelse(res_DMC$diff > 0, "UP", "DOWN")
res_DMC <- res_DMC[, c("chr", "start", "end", "mu1", "mu2", "diff", "diff.se", 
                       "pval", "padj", "pool1")]

#merge with strand
colnames(strand)[2] <- "end"
res_DMC$chr <- as.factor(res_DMC$chr)
strand$chr <- as.factor(strand$chr)
res_DMC <- inner_join(res_DMC, strand, by = c("chr", "end"))
print(paste0("############### Number of DMC : ", nrow(res_DMC)))

#save table
write.table(res_DMC, file = normalizePath(file.path(opt$out, "DMC.txt"), 
                                          mustWork = FALSE), sep = "\t", 
            row.names = FALSE, quote = FALSE)

res_DMC_grange <- GRanges(seqnames = res_DMC$chr, ranges = IRanges(res_DMC$end, res_DMC$end),
                          strand = res_DMC$strand, name = res_DMC$pool1, score = res_DMC$diff)

if(nrow(res_DMC) > 0){
  export(res_DMC_grange, normalizePath(file.path(opt$out, "DMC.bed"), mustWork = FALSE), 
       trackLine=new("BasicTrackLine", name = "DMC", 
                     description = paste0("pool1 (", paste(sample_info$name[sample_info$condition == 1], collapse = ", "),
                                          ") vs pool2 (", paste(sample_info$name[sample_info$condition == 2], collapse = ", "), ")"), 
                     useScore = TRUE))
}

## DMR
if (opt$dmr){
  #source function with qvalue if opt$dmr.type = 'qvalue'
  if(opt$dmr.type == "qvalue"){
    cmd.args <- commandArgs()
    m <- regexpr("(?<=^--file=).+", cmd.args, perl=TRUE)
    path_dmr <- file.path(dirname(regmatches(cmd.args, m)),"DMR.R")
    source(path_dmr)
  }
  
  #find DMR
  try(res_DMR <- callDMR(dmlTest, delta = 0, p.threshold = opt$alpha, 
                     minCG = opt$dmr.numC, pct.sig = opt$dmr.propDMC), 
      silent = TRUE)
  
  if(!is.null(res_DMR)){
    print(paste0("############### Number of DMR : ", nrow(res_DMR)))
  } else {
    print("############### Number of DMR : 0")
    res_DMR <- matrix(ncol = 10, nrow=0)
    colnames(res_DMR) <- c("chr", "start", "end", "length", "nCG",
                           "meanMethy1", "meanMethy2", "diff.Methy", "areaStat", 
                           "pool1")
    res_DMR <- as.data.frame(res_DMR)
  }
  
  res_DMR$pool1 <- ifelse(res_DMR$diff.Methy > 0, "UP", "DOWN")
  
  write.table(res_DMR, file = normalizePath(file.path(opt$out, "DMR.txt"), 
                                            mustWork = FALSE), sep = "\t", 
              row.names = FALSE, quote = FALSE)
  
  res_DMR_grange <- GRanges(seqnames = res_DMR$chr, ranges = IRanges(res_DMR$start, res_DMR$end),
                            name = res_DMR$pool1, score = res_DMR$diff)
  
  if(nrow(res_DMR) > 0){
    export(res_DMR_grange, normalizePath(file.path(opt$out, "DMR.bed"), mustWork = FALSE), 
         trackLine=new("BasicTrackLine", name = "DMR", 
                       description = paste0("pool1 (", paste(sample_info$name[sample_info$condition == 1], collapse = ", "),
                                            ") vs pool2 (", paste(sample_info$name[sample_info$condition == 2], collapse = ", "), ")"), 
                       useScore = TRUE))
  }
  
  if(!is.null(opt$gff)){
    ## gff file
    gff <- import.gff3(opt$gff)
    
    ## Correspondance DMR-gene
    if(sum(gff@elementMetadata@listData$type == "gene", na.rm = TRUE) > 0 & nrow(res_DMR) > 0){
      res_DMR_grange_annot <- GRanges(seqnames = res_DMR$chr, ranges = IRanges(res_DMR$start, res_DMR$end))
      gene_grange <- GRanges(seqnames = seqnames(gff)[gff@elementMetadata@listData$type == "gene"],
                             IRanges(start(gff)[gff@elementMetadata@listData$type == "gene"],
                                     end = end(gff)[gff@elementMetadata@listData$type == "gene"],
                                     names = gff@elementMetadata@listData$Name[gff@elementMetadata@listData$type == "gene"]))
      annotatedDMR <- suppressWarnings(annotatePeakInBatch(res_DMR_grange_annot, 
                                                           AnnotationData=gene_grange, 
                                                           output = "both"))
      
      write.table(as.data.frame(annotatedDMR)[, c("seqnames", "start", "end", 
                                                  "feature", "start_position", 
                                                  "end_position", "insideFeature",
                                                  "distancetoFeature",
                                                  "shortestDistance")], 
                  file = normalizePath(file.path(opt$out, "DMRannoted.txt"), 
                                       mustWork = FALSE), sep = "\t", 
                  row.names = FALSE, quote = FALSE)
      
    }
  }

}


######################### PLOTS

if(opt$plots){
  pdf(file.path(opt$out, "images_DMC.pdf"), title = "Plots from DSS (DMC and DMR)",
      width = 12, height = 10)
  
  #Distribution of the distance between 2 cytosines
  diff <- unlist(sapply(unique(as.character(seqnames(BSobj))), 
                        function(x) diff(as.numeric(start(BSobj))[as.character(seqnames(BSobj)) == x[1]])))
  
  ggplot(data.frame(diff=diff), aes(x = log2(diff))) + 
    geom_density(adjust = 2) + ylab("Density") +
    theme_bw() + xlab(label = "Distance between 2 cytosines (log2)") + ggtitle("Distribution of the distance between 2 cytosines") 
  
  diffDMC <- NULL
  if(nrow(res_DMC) > 0){
    res_DMC <- res_DMC[order(res_DMC$chr, res_DMC$start), ]
    diffDMC <- unlist(sapply(as.character(unique(res_DMC$chr)), function(x) diff(res_DMC$start[res_DMC == x[1]])))
    
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

      #Venn diagram
      if (nrow(number_type) > 1){
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
    cytosines_X_N <- GRanges(seqnames = as.character(seqnames(BSobj)), 
                             ranges = IRanges(as.numeric(start(BSobj)), 
                                              as.numeric(start(BSobj))),
                             X=getCoverage(BSobj, type = "M"),
                             N=getCoverage(BSobj, type = "Cov"))
    
    annotGrange <- GRanges(seqnames = annot$chr, IRanges(annot$start, annot$end))
    
    #proportion by type of region
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
    
    #apply function only on C in a predefine type of region
    overlaps_total <- suppressWarnings(findOverlaps(cytosines_X_N, annotGrange))
    
    if(length(subjectHits(overlaps_total)) > 0){
      notempty <- unique(as.numeric(subjectHits(overlaps_total)))
      prop_by_type <- adply(annot[notempty,], 1, propTypeFunc, .parallel = opt$parallel)
      
      #plot
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
  dist_to_tss <- NULL
  if(!is.null(opt$tss)){
    prop_after_table <- GRanges(seqnames = as.character(seqnames(BSobj)), 
                                ranges = IRanges(as.numeric(start(BSobj)), 
                                                 as.numeric(start(BSobj))),
                                prop=getMeth(BSobj, type = "raw"))
    
    
    #table with TSS
    tss <- read.table(opt$tss, header = TRUE)
    tssGrange <- GRanges(seqnames = tss$chr, IRanges(tss$tss - 5000, tss$tss + 5000))
    
    #methylation proportion by distance to TSS
    tssFunc <- function(x){
      temp <- GRanges(seqnames = x$chr[1], IRanges(x$tss[1] - 5000, x$tss[1] + 5000))
      overlaps <- suppressWarnings(subsetByOverlaps(prop_after_table, temp))
      
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
    
    #apply the function only on C in TSS windows
    overlaps_total <- suppressWarnings(findOverlaps(prop_after_table, tssGrange))
    if(length(subjectHits(overlaps_total)) > 0){
      notempty <- unique(as.numeric(subjectHits(overlaps_total)))
      dist_to_tss <- adply(tss[notempty,], 1, tssFunc, .parallel = opt$parallel)
      
      dist_to_tss <- dist_to_tss[, -c(1:3)]
      dist_to_tss_long <- melt(dist_to_tss, id.vars = c("distance"))
      dist_to_tss_long$variable <- sapply(strsplit(as.character(dist_to_tss_long$variable), "[.]"), "[[", 2)
      
      
      #plot
      ggplot(dist_to_tss_long, 
             aes(x = distance, y = value, colour = variable)) +
        geom_smooth(method="gam", formula = y ~ s(x, k = 50, bs = "cs"), se = FALSE) + 
        ylim(c(0,1)) + theme_bw() + guides(color=guide_legend(title="Samples")) +
        xlab("Distance to TSS") + ylab("Smooth proportion of methylation") +
        ggtitle("Smooth proportion of methylation by distance to TSS")
    }
  }
  
  dev.off()
  
  save(diff, diffDMC, dmc_type, prop_by_type, dist_to_tss, 
       file = normalizePath(file.path(opt$out, "data_for_graph.Rdata"), 
                            mustWork = FALSE))
  }

