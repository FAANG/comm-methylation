#
#----------------------------------------------------------------
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
#----------------------------------------------------------------
#authors :
#---------
#	Piumi Francois (francois.piumi@inra.fr)		software conception and development (engineer in bioinformatics)
#	Jouneau Luc (luc.jouneau@inra.fr)		software conception and development (engineer in bioinformatics)
#	Gasselin Maxime (m.gasselin@hotmail.fr)		software user and data analysis (PhD student in Epigenetics)
#	Perrier Jean-Philippe (jp.perrier@hotmail.fr)	software user and data analysis (PhD student in Epigenetics)
#	Al Adhami Hala (hala_adhami@hotmail.com)	software user and data analysis (postdoctoral researcher in Epigenetics)
#	Jammes Helene (helene.jammes@inra.fr)		software user and data analysis (research group leader in Epigenetics)
#	Kiefer Helene (helene.kiefer@inra.fr)		software user and data analysis (principal invertigator in Epigenetics)
#

library(dplyr)

args=commandArgs(trailingOnly = TRUE)
configFile=args[1]
logFile=args[2]

config=read.table(file=configFile, header=T, sep="\t")

samples=as.character(config[,1])
fileList=as.character(config[,2])
treatment=as.character(config[,3])
colors=as.character(config[,4])

#Read other parameters
IN=file(configFile,open="r")
lines=readLines(IN)
close(IN)

cat("CMD analyse_descriptive.R\n",file=logFile,append=F,sep="")
cat("\tConfiguration file :\t",configFile,"\n",file=logFile,append=T,sep="")
cat("\t--------------------\n",file=logFile,append=T,sep="")
#------- title -------------
idx=grep("^#title",lines)
if (length(idx)==1) {
	title=gsub("^#title\t","",lines[idx])
} else {
	title=""
}
cat("\t\ttitle=",title,"\n",file=logFile,append=T,sep="")
#------- output_dir -------------
idx=grep("^#output_dir",lines)
if (length(idx)==1) {
	output_dir=gsub("^#output_dir\t","",lines[idx])
} else {
	output_dir="."
}
cat("\t\toutput_dir=",output_dir,"\n",file=logFile,append=T,sep="")
#------- min_coverage -------------
idx=grep("^#min_coverage",lines)
if (length(idx)==1) {
	min_coverage=as.numeric(gsub("^#min_coverage\t","",lines[idx]))
} else {
	min_coverage=10
}
cat("\t\tmin_coverage=",min_coverage,"\n",file=logFile,append=T,sep="")
#------- max_coverage -------------
idx=grep("^#max_coverage",lines)
if (length(idx)==1) {
	max_coverage=as.numeric(gsub("^#max_coverage\t","",lines[idx]))
} else {
	max_coverage=500
}
cat("\t\tmax_coverage=",max_coverage,"\n",file=logFile,append=T,sep="")
#------- min_samples_per_condition -------------
idx=grep("^#min_samples_per_condition",lines)
if (length(idx)==1) {
	min_samples_per_condition=as.numeric(gsub("^#min_samples_per_condition\t","",lines[idx]))
	cat("\t\tmin_samples_per_condition=",min_samples_per_condition,"\n",file=logFile,append=T,sep="")
} else {
	min_samples_per_condition=-1
}
#------- sampling_factor ----------------
idx=grep("^#sampling_factor",lines)
if (length(idx)==1) {
	sampling_factor=as.numeric(gsub("^#sampling_factor\t","",lines[idx]))
	if (sampling_factor>1 | sampling_factor<=0) {
		cat("\t\tsampling_factor should be between ]0;1]. Reset to 1.\n",file=logFile,append=T,sep="")
		sampling_factor=1
	}
	cat("\t\tsampling_factor=",sampling_factor,"\n",file=logFile,append=T,sep="")
} else {
	sampling_factor=1
	cat("\t\tno sampling (sampling factor=1)\n",file=logFile,append=T,sep="")
}
#------- output_tab_file ----------------
idx=grep("^#output_table_file",lines)
if (length(idx)==1) {
	output_tab_file=gsub("^#output_table_file\t","",lines[idx])
	if (length(grep("/",output_tab_file))==0) {#Sortie dans output_dir
		output_tab_file=paste(output_dir,"/",output_tab_file,sep="")
	}
	if (basename(output_tab_file)==output_tab_file) {
		paste(output_dir,"/",output_tab_file,sep="")
	}
	cat("\t\toutput_table_file=",output_tab_file,"\n",file=logFile,append=T,sep="")
} else {
	output_tab_file=""
	cat("\t\tno output for CpG table\n",file=logFile,append=T,sep="")
}
#------- do_pca ----------------
idx=grep("^#produce_pca",lines)
if (length(idx)==1) {
	do_pca=gsub("^#produce_pca\t","",lines[idx])
	do_pca=toupper(do_pca)
	if (do_pca=="NO" | do_pca=="N") {
		do_pca=FALSE
	} else {
		do_pca=TRUE
	}
} else {
	do_pca=TRUE
}
cat("\t\tproduce_pca=",do_pca,"\n",file=logFile,append=T,sep="")
#------- do_hclust ----------------
idx=grep("^#produce_hclust",lines)
if (length(idx)==1) {
	do_hclust=gsub("^#produce_hclust\t","",lines[idx])
	do_hclust=toupper(do_hclust)
	if (do_hclust=="NO" | do_hclust=="N") {
		do_hclust=FALSE
	} else {
		do_hclust=TRUE
	}
} else {
	do_hclust=TRUE
}
cat("\t\tproduce_hclust=",do_hclust,"\n",file=logFile,append=T,sep="")
#------- pca_scaling ----------------
idx=grep("^#pca_scaling",lines)
if (length(idx)==1) {
	pca_scaling=gsub("^#pca_scaling\t","",lines[idx])
	pca_scaling=toupper(pca_scaling)
	if (pca_scaling=="YES" | pca_scaling=="Y") {
		pca_scaling=TRUE
	} else {
		pca_scaling=FALSE
	}
} else {
	pca_scaling=TRUE
}
cat("\t\tpca_scaling=",pca_scaling,"\n",file=logFile,append=T,sep="")


bismarks=list()
for (i in 1:length(fileList)) {
	fileIn=fileList[i]
	sample=samples[i]
	cat("\tReading ",fileIn," for sample ",sample,"...\n",file=logFile,append=T,sep="")
	cat("\tReading ",fileIn," for sample ",sample,"...\n",sep="")
	bismark=read.table(file=fileIn,sep="\t",header=T,row.names=NULL)
	CpG_position=paste(as.character(bismark[,1]),":",as.character(bismark[,2]),sep="")
	bismark=cbind(CpG_position,bismark[,c(3,ncol(bismark))])
	colnames(bismark)=c("Position","Coverage","pct_methylated")
	bismarks[[sample]]=bismark
}

#Dplyr stopped here
treatments=unique(treatment)
cat("\tFiltering coverages ...\n",file=logFile,append=T,sep="")
kept=c()
for (ttt in treatments) {
	samplesInCond=samples[treatment==ttt]
	unionCounts=c()
	cat("\t\tLooking for condition ",ttt," ...\n",file=logFile,append=T,sep="")
	cat("\t\tLooking for condition ",ttt," ...\n",sep="")
	for (sample in samplesInCond) {
		bismark=as_data_frame(bismarks[[sample]])
		cat("\t\t\tFound ",nrow(bismark)," CpG for sample ",sample,"...\n",file=logFile,append=T,sep="")
		cat("\t\t\tFound ",nrow(bismark)," CpG for sample ",sample,"...\n",sep="")
		sel=select(filter(bismark,between(Coverage,min_coverage,max_coverage)),Position)
		cat("\t\t\tKept ",nrow(sel)," CpG for sample ",sample,"...\n",file=logFile,append=T,sep="")
		cat("\t\t\tKept ",nrow(sel)," CpG for sample ",sample,"...\n",sep="")
		unionCounts=c(unionCounts,as.character(sel[,1]$Position))
	}
	t=table(unionCounts)
	sel=names(t)[t>=min_samples_per_condition]
	cat("\t\tKept ",length(sel)," CpG for condition ",ttt,"...\n",file=logFile,append=T,sep="")
	kept=c(kept,sel)
}
t=table(kept)
kept=names(t)[t==length(treatments)]
cat("Kept ",length(kept)," CpG for all conditions ...\n",file=logFile,append=T,sep="")
cat("Kept ",length(kept)," CpG for all conditions ...\n",sep="")

if (sampling_factor<1) {
	kept=sample(kept,round(length(kept)*sampling_factor))
	cat("Kept ",length(kept)," CpG after sampling  (sampling factor=",sampling_factor,") ...\n",file=logFile,append=T,sep="")
	cat("Kept ",length(kept)," CpG after sampling  (sampling factor=",sampling_factor,") ...\n",sep="")
}

cat("Creating final table ...\n",file=logFile,append=T,sep="")
cat("Creating final table ...\n",sep="")
kept=data_frame("Position"=kept)
for (ttt in treatments) {
	samplesInCond=samples[treatment==ttt]
	for (sample in samplesInCond) {
		cat("\tTreating lines for sample ",sample," ...\n",file=logFile,append=T,sep="")
		cat("\tTreating lines for sample ",sample," ...\n",sep="")
		bismark=as_data_frame(bismarks[[sample]])
		kept=select(left_join(kept,select(bismark,Position,pct_methylated),by=c("Position")),everything())
		colnames(kept)[ncol(kept)]=sample
	}
}
tab=select(kept,-Position)

#Imputation d'une valeur moyenne par condition pour les valeurs manquantes
#for (ttt in treatments) {
#	samplesInCond=samples[treatment==ttt]
#	colNums=match(samplesInCond,colnames(kept))
#	tabCondition=select(kept,colNums)
#	cat("\tImputation of missing values for condition ",ttt," ...\n",file=logFile,append=T,sep="")
#	cat("\tImputation of missing values for condition ",ttt," ...\n",sep="")
#	meanPerCondition=apply(tabCondition,1,FUN=function(x) {mean(x,na.rm=TRUE)})
#	for (sample in samplesInCond) {
#		cat("\t\tImputation of missing values for sample ",sample," ...\n",file=logFile,append=T,sep="")
#		cat("\t\tImputation of missing values for sample ",sample," ...\n",sep="")
#		sel=is.na(kept[,sample])
#		kept[sel,sample]=meanPerCondition[sel]
#	}
#}

#DEBUG
#tab=tab[1:10000,]
if (output_tab_file != "") {
	write.table(file=output_tab_file,kept,row.names=F,sep="\t",quote=F)
}

if (!do_pca & !do_hclust) {
	cat("\tStopping because neither principal component nor Hierarchical clustering analyses have been requested.\n",file=logFile,append=T,sep="")
	q(save="no")
}

output.file=paste(output_dir,"/Descriptive analyses - ",title,".pdf",sep="")
if (sampling_factor!=1) {
	output.file=gsub(".pdf",paste(" - sampling",sampling_factor,".pdf",sep=""),output.file)
}

cat("\tProducing pdf ",output.file," ...\n",file=logFile,append=T,sep="")
pdf(output.file)

if (do_hclust) {
#####################
# Clustering 
#####################
names(colors)=samples
for (distFun in c("Euclidean","Correlation")) {
	if (distFun=="Euclidean") {
		fit_profondeur=hclust(dist(t(tab)),method="ward")
	} else {
		fit_profondeur=hclust(
			as.dist(1-cor(tab,use='pairwise.complete.obs',method='pearson')),
			method="ward")
	}
	dendrogram=as.dendrogram(fit_profondeur,hang=0.1)
	dendrogram_coloured= dendrapply(dendrogram,FUN=function(node) {
		if(is.leaf(node)) {
			a <- attributes(node)
			color=colors[a$label]
			attr(node, "nodePar") <- c(a$nodePar, list(lab.col = color))
		}
		node
		}
	)
	plot(
		dendrogram_coloured,
		main=paste(distFun," clustering on ",title,sep=""),
	)
}
}

if (do_pca) {
###################
# ACP
###################
library(FactoMineR)
Mt=t(tab)
nbGenes=ncol(Mt)
cn=colnames(Mt)
Mt=data.frame(
	Mt,
	treatment
)
colnames(Mt)[ncol(Mt)]="Groups"
posQualif=nbGenes+1

qualiColors=c()
for (c in colors) {
	if (c %in% qualiColors) {
		next
	}
	qualiColors=c(qualiColors,c)
}


nbAxes=ncol(tab)
RESt<-PCA(Mt,quali.sup=posQualif,scale.unit=pca_scaling, ncp=nbAxes, graph = FALSE)

barplot(RESt$eig[1:nbAxes,2],
	main=paste("PCA on ",title,"\n% of total variance explained by axes",sep=""),
	names.arg=paste("Axis",1:nbAxes),
	ylab="% of variance",las=2
)

explainedVar=RESt$eig[1:nbAxes,2]
names(explainedVar)=c(1:length(explainedVar))
sel=explainedVar==0 | is.na(explainedVar)
if (sum(sel)!=0) {
	sel=names(explainedVar)[sel]
	sel=as.numeric(sel)
	nbAxes=max(sel)-1
}

idx=0
for (i in 1:(nbAxes-1)) {
	j=i+1
	hab=posQualif+idx
	aa=cbind.data.frame(as.character(Mt[,hab]),RESt$ind$coord)
	bb=coord.ellipse(aa,bary=TRUE,axes=c(i,j))
	plot.PCA(RESt,
		axes=c(i, j),
		label=c("ind","quali.sup"),
		habillage=hab,col.hab=qualiColors,
		title=paste("PCA on ",title," - Axis #",i," & #",j,sep=""),
		ellipse=bb,new.plot=FALSE
	)
}
}
#------------------
# End of analyses
#------------------
dev.off()
cat("OUT ",output.file,"\n",file=logFile,append=T,sep="")
cat("STATUS OK\n",file=logFile,append=T,sep="")
