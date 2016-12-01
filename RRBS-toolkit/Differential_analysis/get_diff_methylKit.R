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
#----------------------------------------------------------------------
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

library(methylKit)

args=commandArgs(trailingOnly = TRUE)
configFile=args[1]
logFile=args[2]
tmpDir=args[3]
pid=args[4]

config=read.table(file=configFile, header=T, sep="\t")


fileList=as.character(config[,"File"])
fileList2=c()
noFile=0
for (file in fileList) {
	noFile=noFile+1
	file2=paste(tmpDir,"/",basename(file),".",pid,".",noFile,sep="")
	fileList2=c(fileList2,file2)
}
fileList=fileList2

sample.id=as.character(config[,"Sample"])

#The first condition listed in config file is the reference condition
reference_condition=as.character(config[1,"Condition"])
alternative_condition=unique(as.character(config[,"Condition"]))
alternative_condition=alternative_condition[alternative_condition!=reference_condition]
config[,"Condition"]=factor(as.character(config[,"Condition"]),levels=c(reference_condition,alternative_condition))
treatment=as.numeric(config[,"Condition"]) - 1

#Read other parameters
IN=file(configFile,open="r")
lines=readLines(IN)
close(IN)

cat("CMD get_diff_methyl.R\n",file=logFile,append=F,sep="")
cat("FLAVOR methylKit\n\n",file=logFile,append=T,sep="")
cat("\tConfiguration file :\t",configFile,"\n",file=logFile,append=T,sep="")
cat("\t--------------------\n",file=logFile,append=T,sep="")
#------- min_coverage -------------
idx=grep("^#min_coverage1",lines)
if (length(idx)==1) {
	min_coverage=as.numeric(gsub("^#min_coverage1\t","",lines[idx]))
} else {
	min_coverage=10
}
cat("\t\tmin_coverage=",min_coverage,"\n",file=logFile,append=T,sep="")
#------- max_coverage -------------
idx=grep("^#max_coverage1",lines)
if (length(idx)==1) {
	max_coverage=as.numeric(gsub("^#max_coverage1\t","",lines[idx]))
	cat("\t\tmax_coverage=",max_coverage,"\n",file=logFile,append=T,sep="")
} else {
	max_coverage=NULL
	cat("\t\tmax_coverage= no limit\n",file=logFile,append=T,sep="")
}
#------- destranded -------------
idx=grep("^#destranded",lines)
if (length(idx)==1) {
	destranded=gsub("^#destranded\t","",lines[idx])
	if (destranded=="FALSE") {
		destranded=FALSE
	} else {
		destranded=TRUE
	}
} else {
	destranded=FALSE
}
cat("\t\tdestranded=",destranded,"\n",file=logFile,append=T,sep="")
#------- tiling -------------
idx=grep("^#tiling\t",lines)
if (length(idx)==1) {
	tiling=gsub("^#tiling\t","",lines[idx])
	if (tiling=="TRUE") {
		tiling=TRUE
	} else {
		tiling=FALSE
	}
} else {
	tiling=FALSE
}
cat("\t\ttiling=",tiling,"\n",file=logFile,append=T,sep="")
#------- tiling_window -------------
idx=grep("^#tiling_window",lines)
if (length(idx)==1) {
	tiling_window=as.numeric(gsub("^#tiling_window\t","",lines[idx]))
} else {
	tiling_window=1000
}
cat("\t\ttiling_window=",tiling_window,"\n",file=logFile,append=T,sep="")
#------- tiling_step -------------
idx=grep("^#tiling_step",lines)
if (length(idx)==1) {
	tiling_step=as.numeric(gsub("^#tiling_step\t","",lines[idx]))
} else {
	tiling_step=1000
}
cat("\t\ttiling_step=",tiling_step,"\n",file=logFile,append=T,sep="")
#------- stat_value -------------
idx=grep("^#stat_value",lines)
if (length(idx)==1) {
	stat_value=gsub("^#stat_value\t","",lines[idx])
	stat_value=tolower(stat_value)
	if (stat_value!="pvalue") {
		stat_value="qvalue"
	}
} else {
	stat_value="qvalue"
}
stat_value=tolower(stat_value)
cat("\t\tstat_value=",stat_value,"\n",file=logFile,append=T,sep="")
#------- stat_threshold1 -------------
idx=grep("^#stat_threshold1",lines)
if (length(idx)==1) {
	stat_threshold1=as.numeric(gsub("^#stat_threshold1\t","",lines[idx]))
} else {
	stat_threshold1=0.01
}
cat("\t\tstat_threshold1=",stat_threshold1,"\n",file=logFile,append=T,sep="")
idx=grep("^#stat_threshold2",lines)
if (length(idx)==1) {
	stat_threshold2=as.numeric(gsub("^#stat_threshold2\t","",lines[idx]))
} else {
	stat_threshold2=0.05
}
cat("\t\tstat_threshold2=",stat_threshold2,"\n",file=logFile,append=T,sep="")
#------- methdiff_threshold1 -------------
idx=grep("^#methdiff_threshold1",lines)
if (length(idx)==1) {
	methdiff_threshold=as.numeric(gsub("^#methdiff_threshold1\t","",lines[idx]))
	if (methdiff_threshold<=1) {
		methdiff_threshold=methdiff_threshold*100
	}
} else {
	methdiff_threshold=25
}
cat("\t\tmethdiff_threshold1=",methdiff_threshold,"\n",file=logFile,append=T,sep="")
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
#------- min_per_group
idx=grep("^#min_per_group",lines)
if (length(idx)==1) {
	min_per_group=as.numeric(gsub("^#min_per_group\t","",lines[idx]))
} else {
	min_per_group=min(table(treatment))
}
cat("\t\tmin_per_group=",min_per_group,"\n",file=logFile,append=T,sep="")
#--------------------------------
cat("\t--------------------\n",file=logFile,append=T,sep="")

cat("\t",date(),"\tRead data ...\n",file=logFile,append=T,sep="")
mkData=read(as.list(fileList), sample.id=as.list(sample.id), assembly="Btau6", treatment=treatment, context="CpG")

cat("\t",date(),"\tFiltering on coverage ...\n",file=logFile,append=T,sep="")
filtered.mkData=filterByCoverage(mkData, lo.count=min_coverage, hi.count=max_coverage, lo.perc = NULL, hi.perc = NULL)

if (tiling) {#Tiling analysis
	cat("\t",date(),"\tTiling data ...\n",file=logFile,append=T,sep="")
	filtered.mkData=tileMethylCounts(filtered.mkData,win.size=tiling_window,step.size=tiling_step)
}

cat("\t",date(),"\tGrouping data ...\n",file=logFile,append=T,sep="")
#Provoque une erreur avec destranded=TRUE :
#Error in `$<-.data.frame`(`*tmp*`, "strand", value = "+") :
#  replacement has 1 row, data has 0
#mkMeth=unite(filtered.mkData,destrand=destranded, min_per_group=min(table(treatment)))
#
#LJ 20150930 : certainement du au fait que dans les fichiers en entee, le
#strand '+' est indique par 'F' au lieu de '+"
mkMeth=unite(filtered.mkData,destrand=FALSE, min.per.group=as.integer(min_per_group))

nbCpGTested=nrow(mkMeth)
cat("INFO number of CpGs tested by methylKit=",nbCpGTested,"\n",file=logFile,append=T,sep="")

cat("\t",date(),"\tCalculate methylKit ...\n",file=logFile,append=T,sep="")
mkDiff=calculateDiffMeth(mkMeth)

#Save RData for backup
#save(list=c("mkData","filtered.mkData","mkMeth","mkDiff"),file=paste(output_dir,"/methylKit.RData",sep=""))

mkDiff2=getData(mkDiff)
mkMeth2=getData(mkMeth)

pvalues=mkDiff2[,stat_value]
mdiff=as.numeric(as.character(mkDiff2[,"meth.diff"]))

selectSignificative <- function (stat_threshold,methdiff_threshold) {
	selDMC=which(pvalues<stat_threshold & abs(mdiff)>methdiff_threshold)

	if (sum(selDMC!=0)) {
		chr=as.character(mkDiff2[selDMC,"chr"])
		start=as.numeric(as.character(mkDiff2[selDMC,"start"]))
		pv=as.numeric(as.character(mkDiff2[selDMC,stat_value]))
		methDiff=as.numeric(as.character(mkDiff2[selDMC,"meth.diff"]))

		coordsDMC=paste(chr,".",start,sep="")
		coordsMeth=paste(as.character(mkMeth2[,"chr"]),".",as.numeric(as.character(mkMeth2[,"start"])),sep="")

		selMeth=which(coordsMeth %in% coordsDMC)

		#selectedSummary=coordsDMC
		selectedSummary=cbind(coordsDMC,chr,start,start+1)

		for (i in 1:length(sample.id)) {
			selectedSummary=cbind(selectedSummary,
					      mkMeth2[selMeth,paste("coverage",i,sep="")],
					      mkMeth2[selMeth,paste("numCs",i,sep="")]
			)
		}
		selectedSummary=cbind(selectedSummary,pv,methDiff)
		selectedSummary=as.data.frame(selectedSummary)
		colnames(selectedSummary)=c("Position","Chromosome","Start","End",paste(c("Cov","FreqC"),rep(sample.id,each=2),sep=""),stat_value,"Methyl diff")

		selectedSummary
	} else {
		c()
	}
}

plotDMC <- function(ratio,cover,label,pv) {
	#Save default config
	def.par <- par(no.readonly = TRUE)

	nullPV=pv==0
	minPVNotNull=min(pv[!nullPV])
	q=seq(log10(minPVNotNull),max(log10(pv)),(max(log10(pv))-log10(minPVNotNull))/100)
	q=c(log10(minPVNotNull*0.1),q)
	palette=rev(heat.colors(102))

	pv[nullPV]=minPVNotNull*0.1
	pv=log10(pv)
	rcp=cbind(ratio,cover,pv)
	ag=aggregate(rcp,by=list(ratio,cover),median)
	ratio=ag[,1]
	cover=ag[,2]
	pv=ag[,"pv"]

	colors=rep(0,length(pv))
	for (idxColor in 2:length(q)) {
		sel= pv>q[idxColor-1] & pv<=q[idxColor]
		colors[sel]=palette[idxColor]
	}
	colors[pv==log10(minPVNotNull*0.1)]=palette[1]

	for (loop in 1:2) {
	par(bg="gray")
	layout(matrix(c(1,2),1,2,byrow=TRUE),widths=c(4,1),heights=c(1,1))
	par(mar=c(5,4,4,0))
	if (loop==1) {
		ylim=c(min(cover),max(cover))
		pointStyle="."
		pointCex=3
		lab=label
	} else {
		ylim=c(min(cover),75)
		pointStyle=19
		pointCex=1
		lab=paste(label,"\n(Zoom on coverage<75)",sep="")
	}
	plot(x=ratio,cover,pch=pointStyle,cex=pointCex,col=colors,xlab="% C/T",ylab="Coverage",main=lab,ylim=ylim)
	abline(v=c(methdiff_threshold/100,(100-methdiff_threshold)/100),lty=2,col="black")
	par(mar=c(5,4,4,2))
	plot(x=c(),y=c(),xlim=c(0,1),ylim=c(0,101),xaxt="n",xlab="",yaxt="n",ylab="",
	     main=paste("log10(",stat_value,")",sep=""),cex.main=0.8,
	     #No inner image inside plot <=> ylim are really the limit of y axis
	     #See : http://rexpo.blogspot.fr/2010/11/remove-inner-margins-in-r-plots.html
	     yaxs="i"
	)
	for (i in 1:(length(q)-1)) {
		rect(0,(i-1),1,i,col=palette[i],border=palette[i])
	}
	axis(side=4,at=(0:10)*10,labels=c("-Inf",round(q[(1:10)*10],0)))
	}

	#Resore default values
	par(def.par)
}

#######################################################
# Plot % C/T between 2 samples
#######################################################
plotRatio_2Samples <-function(ratio1,ratio2,smp1,smp2,label,pv) {
	minPVNotNull=min(pv[pv!=0])
	q=seq(min(log10(minPVNotNull)),max(log10(pv)),(max(log10(pv))-min(log10(minPVNotNull)))/100)
	q=c(q[1]-(q[2]-q[1]),q)
	palette=rev(heat.colors(102))
	colors=rep(0,length(pv))
	for (idxColor in 2:length(q)) {
		sel= log10(pv)>q[idxColor-1] & log10(pv)<=q[idxColor]
		colors[sel]=palette[idxColor]
	}
	colors[pv==0]=palette[1]
	par(bg="gray")
	layout(matrix(c(1,2),1,2,byrow=TRUE),widths=c(4,1),heights=c(1,1))
	par(mar=c(5,4,4,0))
	plot(x=ratio1,y=ratio2,col=colors,pch=".",cex=3,
	     xlab=paste("% C/T ",smp1,sep=""),ylab=paste("% C/T ",smp2,sep=""),main=label)
	par(mar=c(5,4,4,2))
	plot(x=c(),y=c(),xlim=c(0,1),ylim=c(0,101),xaxt="n",xlab="",yaxt="n",ylab="",
	     main="log10(pvalue)",cex.main=0.8,
	     #No inner image inside plot <=> ylim are really the limit of y axis
	     #See : http://rexpo.blogspot.fr/2010/11/remove-inner-margins-in-r-plots.html
	     yaxs="i"
	)
	for (i in 1:(length(q)-1)) {
		rect(0,(i-1),1,i,col=palette[i],border=palette[i])
	}
	axis(side=4,at=(0:10)*10,labels=c("-Inf",round(q[(1:10)*10],1)))
}

#Usage :
#-------
#
#smp1=sample.id[1]
#smp2=sample.id[3]
#cov1=as.numeric(as.character(selResults[,paste("Cov",smp1,sep="")]))
#ratio1=as.numeric(as.character(selResults[,paste("FreqC",smp1,sep="")]))/cov1
#cov2=as.numeric(as.character(selResults[,paste("Cov",smp2,sep="")]))
#ratio2=as.numeric(as.character(selResults[,paste("FreqC",smp2,sep="")]))/cov2
#plotRatio_2Samples(ratio1,ratio2,smp1,smp2,paste("% C/T between ",smp1," and ",smp2,sep=""),pv)
#######################################################

#######################################################
#Pair plots of % C/T for all samples
#######################################################
plotRatio_AllSamples <- function(selResults) {
	tabRatio=type.convert(as.matrix(selResults[,grep("^FreqC",colnames(selResults))])) / type.convert(as.matrix(selResults[,grep("^Cov",colnames(selResults))]))
	colnames(tabRatio)=gsub("FreqC","Smp_",colnames(tabRatio))
	
	pv=as.numeric(as.character(selResults[,stat_value]))
	idx=order(pv,decreasing=F)#[sample(1:length(pv),1000)]
	tabRatio=tabRatio[idx,]
	pv=pv[idx]
	
	minPVNotNull=min(pv[pv!=0])
	q=seq(min(log10(minPVNotNull)),max(log10(pv)),(max(log10(pv))-min(log10(minPVNotNull)))/100)
	q=c(q[1]-(q[2]-q[1]),q)
	palette=rev(heat.colors(102))
	colors=rep(0,length(pv))
	for (idxColor in 2:length(q)) {
		sel= log10(pv)>q[idxColor-1] & log10(pv)<=q[idxColor]
		colors[sel]=palette[idxColor]
	}
	colors[pv==0]=palette[1]
	fmla <- as.formula(paste("~ ", paste(colnames(tabRatio), collapse= "+")))
	par(bg="gray")
	pairs(fmla,data=tabRatio,pch=".",col=colors,main="% C/T pair plots")
}

#Usage :
#-------
#
#plotRatio_AllSamples(selResults)
#######################################################

selResults=selectSignificative(stat_threshold1,methdiff_threshold)
if (!is.null(selResults)) {#There are some results
	nbSignif=nrow(selResults)
	cat("\t",date(),"\tProduces output ...\n",file=logFile,append=T,sep="")

	output.file=paste(output_dir,"/MethylKit - ",title," - ",stat_value,stat_threshold1,sep="")

	pdf(paste(output.file,".pdf",sep=""))
	
	#Histogramme des pValues brutes
	rawp=as.numeric(as.character(mkDiff2[,"pvalue"]))
	hist(rawp,xlab="Raw pValue",main="Histogram of raw pValues",nclass=100)
	hist(rawp[rawp<0.01],xlab="Raw pValue",main="Histogram of raw pValues\n(Zoom on pvalue<1%)",nclass=100)

	#Histogramme des differences de méylation pour les réltats jugéignificatifs
	hTrue=hist(as.numeric(as.character(selResults[,"Methyl diff"])),nclass=100,plot=F)
	CpGSelected=as.character(selResults[,"Position"])
	mdOthers=mkDiff2[!(paste(mkDiff2[,"chr"],".",mkDiff2[,"start"],sep="") %in% CpGSelected),"meth.diff"]
	hFalse=hist(mdOthers,nclass=100,plot=F)

	plot(hTrue,xlab="Difference in methylation",main="Distribution of difference in methylation between conditions",col="#FF000088")
	plot(hFalse,col="#88888888",add=T)
	abline(v=c(-methdiff_threshold,methdiff_threshold),lty=2,col="green")
	legend(x="topright",legend=c("Significative results","Other results"),fill=c("#FF000088","#88888888"))

	#Plots de controle proposes par methylKit
	getCorrelation(mkMeth,plot=T)
	clusterSamples(mkMeth, dist="correlation" , method="ward" , plot=T)
	PCASamples(mkMeth, screeplot=T)
	PCASamples(mkMeth)

	#Plot coverag vs ratio
	for (i in 1:length(sample.id)) {
		smp=sample.id[i]
		coverages=as.numeric(as.character(selResults[,paste("Cov",smp,sep="")]))
		ratios=as.numeric(as.character(selResults[,paste("FreqC",smp,sep="")]))/coverages
		pv=as.numeric(as.character(selResults[,stat_value]))
		idx=order(pv,decreasing=T)
		coverages=coverages[idx]
		ratios=ratios[idx]
		pv=pv[idx]
		plotDMC(ratios,coverages,smp,pv)
	}

	#Distributiobn methylation pour les sondes significatives
	par(bg="gray")
	for (stat_threshold in c(stat_threshold1,stat_threshold2)) {
	for (i in 1:length(sample.id)) {
		smp=sample.id[i]
		selResults=selectSignificative(stat_threshold,methdiff_threshold)
		coverages=as.numeric(as.character(selResults[,paste("Cov",smp,sep="")]))
		ratios=as.numeric(as.character(selResults[,paste("FreqC",smp,sep="")]))/coverages
		hist(ratios,nclass=100,xlab="% methylation",main=paste("Methylation distribution in DMC for ",smp,"\n",stat_value,"=",stat_threshold,sep=""))
	}
	}

	dev.off()

	#Output for stat_threshold1
	selResults=selResults[,-grep("Position",colnames(selResults))]
	selResults[,ncol(selResults)]=-as.numeric(as.character(selResults[,ncol(selResults)]))

	hypo_hyper=rep("hypermeth",nrow(selResults))
	hypo_hyper[selResults[,ncol(selResults)]<0]="hypometh"
	selResults=cbind(selResults,hypo_hyper)
	colnames(selResults)[ncol(selResults)]=paste("Methylation state in ",reference_condition,sep="")

	output.file=paste(output_dir,"/MethylKit - ",title," - ",stat_value,stat_threshold1,sep="")
	write.table(file=paste(output.file,".txt",sep=""),selResults,sep="\t",row.names=F,quote=F)

	#Output for stat_threshold1 : needed to extend DMRs
	selResults=selectSignificative(stat_threshold2,methdiff_threshold)
	selResults=selResults[,-grep("Position",colnames(selResults))]
	selResults[,ncol(selResults)]=-as.numeric(as.character(selResults[,ncol(selResults)]))

	hypo_hyper=rep("hypermeth",nrow(selResults))
	hypo_hyper[selResults[,ncol(selResults)]<0]="hypometh"
	selResults=cbind(selResults,hypo_hyper)
	colnames(selResults)[ncol(selResults)]=paste("Methylation state in ",reference_condition,sep="")

	output.file=paste(output_dir,"/MethylKit - ",title," - ",stat_value,stat_threshold2,sep="")
	write.table(file=paste(output.file,".txt",sep=""),selResults,sep="\t",row.names=F,quote=F)
} else {
	nbSignif=0

	selResults=selectSignificative(stat_threshold2,methdiff_threshold)

	if (is.null(selResults)) {
		selResults=matrix(nrow=0,ncol=6+length(sample.id)*2)
		colnames(selResults)=c("Position","Chromosome","Start","End",
					paste(c("Cov","FreqC"),rep(sample.id,each=2),sep=""),
					stat_value,"Methyl diff"
				     )
	}

	selResults=selResults[,-grep("Position",colnames(selResults))]
	selResults[,ncol(selResults)]=-as.numeric(as.character(selResults[,ncol(selResults)]))

	if (nrow(selResults)>0)  {
		hypo_hyper=rep("hypermeth",nrow(selResults))
		hypo_hyper[selResults[,ncol(selResults)]<0]="hypometh"
	} else {
		hypo_hyper=c()
	}
	selResults=cbind(selResults,hypo_hyper)
	colnames(selResults)[ncol(selResults)]=paste("Methylation state in ",reference_condition,sep="")

	output.file=paste(output_dir,"/MethylKit - ",title," - ",stat_value,stat_threshold2,sep="")
	write.table(file=paste(output.file,".txt",sep=""),selResults,sep="\t",row.names=F,quote=F)
}

cat("RESULT number of DMCs detected by methylKit=",nbSignif,"\n",file=logFile,append=T,sep="")
cat("OUT ",output.file,".txt\n",file=logFile,append=T,sep="")
cat("STATUS OK\n",file=logFile,append=T,sep="")
quit(save="no",status=0)

