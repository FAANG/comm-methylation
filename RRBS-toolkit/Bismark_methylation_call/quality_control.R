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

args <- commandArgs(trailingOnly = TRUE)

dir_data=as.character(args[1])
dir_name=basename(dir_data)

pdf(paste(dir_data,"/quality_control/Mapping quality controls.pdf",sep=""))

##################
# R1-R2 Distance #
##################
R1R2_distance_file=paste(dir_data,"/extract/distance_R1R2.txt",sep="")
if (file.exists(R1R2_distance_file)) {
	distance=read.csv(file=R1R2_distance_file,header=T, sep="\t"
	)
	distance=distance[,1]
	
	hist(distance,nclass=100,main="Distance R2-R1",xlab="Distance")
	sel=abs(distance)<=100
	hist(distance[sel],nclass=100,main="Distance R2-R1\nZoom [-100,100]",xlab="Distance")
}

##################
#   Coverage     #
##################
tab=read.csv(file=paste(dir_data,"/extract/synthese_CpG.txt",sep=""),
	       header=T, sep="\t"
)
colnames(tab)=c("Chromosome","Position","Coverage","# methylated","% methylated")

coverage=as.matrix(summary(tab[,"Coverage"]))
coverage=cbind(rownames(coverage),coverage)
colnames(coverage)=c("Category","Coverage")
pct5=round(sum(tab[,"Coverage"]>=5)/nrow(tab)*1000)/10
pct10=round(sum(tab[,"Coverage"]>=10)/nrow(tab)*1000)/10
pct5_500=round(sum(tab[,"Coverage"]>=5 & tab[,"Coverage"]<=500)/nrow(tab)*1000)/10
pct10_500=round(sum(tab[,"Coverage"]>=10 & tab[,"Coverage"]<=500)/nrow(tab)*1000)/10
pct500=round(sum(tab[,"Coverage"]>500)/nrow(tab)*1000)/10
coverage=rbind(coverage,
	       cbind("% of positions with coverage>=5",pct5),
	       cbind("% of positions with coverage in [5;500]",pct5_500),
	       cbind("% of positions with coverage>=10",pct10),
	       cbind("% of positions with covera in [10;500]",pct10_500),
	       cbind("% of positions with coverage>500",pct500)
)
write.table(file=paste(dir_data,"/quality_control/",dir_name,"_coverage_summary.txt",sep=""),
	    coverage,sep="\t",quote=F,row.names=F
)

pct90=quantile(tab[,"Coverage"],seq(0,1,0.1))[10]
res=c()
for (i in 1:pct90) {
	res=c(res,sum(tab[,"Coverage"]==i))
}

res=c(res,sum(tab[,"Coverage"]>pct90))
names(res)=c(1:pct90,paste(">",pct90,sep=""))

barplot(height=res,
     width=1,space=0,,xaxt="n",
     main=paste("Sample ",dir_data," - Coverage distribution",sep=""),
     xlab="Coverage",ylab="# of covered CG"
)
axis(side=1,at=1:length(res)-0.5,labels=names(res),las=2)

med=coverage["Median",2]
abline(v=med,col="red")
avg=coverage["Mean",2]
abline(v=avg,col="black")
firstQT=coverage["1st Qu.",2]
abline(v=firstQT,col="blue")
lastQT=coverage["3rd Qu.",2]
abline(v=lastQT,col="green")
legend(x="topright",fill=c("blue","red","black","green"),
       legend=c("1st quartile","median","mean","3rd quartile")
)


#----------------------------
# Couverture par chromosome
#----------------------------
chromosomes=unique(as.character(tab[,"Chromosome"]))
chromosomes=chromosomes[grep("^(chr)?([0-9XY]*)$",chromosomes)]
chrNum=gsub("chr","",grep("(chr)?[0-9]",chromosomes,value=T))
chrLetter=gsub("chr","",grep("(chr)?[^0-9]",chromosomes,value=T))
chrNum=chrNum[order(as.numeric(chrNum))]
chrLetter=chrLetter[order(chrLetter)]
chromosomes=c(chrNum,chrLetter)

for (threshold in c(5,10)) {
for (loop in 1:2) {
	res=c()
	for (chr in chromosomes) {
		sel=gsub("^chr","",tab[,"Chromosome"])==chr
		if (sum(sel)>=1000) {
			if (loop==1) {
				pct5=round(sum(tab[sel,"Coverage"]>=threshold)/sum(sel)*1000)/10
				stitle=paste(">=",threshold,sep="")
			} else {
				pct5=round(sum(tab[sel,"Coverage"]>=threshold & tab[sel,"Coverage"]<=500)/sum(sel)*1000)/10
				stitle=paste(" in [",threshold,";500]",sep="")
			}
			res=rbind(res,cbind(chr,pct5))
		}
	}
	if (!is.null(nrow(res))) {
		barplot(height=as.numeric(res[,2]),xaxt="n",
		     width=1,space=0,
		     main=paste("% of coverage",stitle,"\nper chromosome",sep=""),
		     xlab="",ylab="% of coverage",
		     ylim=c(0,100)
		)
		axis(at=1:length(chromosomes)-0.5,labels=chromosomes,side=1,las=2)
	}
}
}

##################
#  Methylation   #
##################

#Average methylation on uniquely mapped positions
#methyl=round(sum(tab[,"# methylated"])/sum(tab[,"Coverage"])*1000)/10
methyl=round(mean(tab[,"# methylated"]/tab[,"Coverage"])*1000)/10
	hypo=round(sum((tab[,"# methylated"]/tab[,"Coverage"])<=0.2)/nrow(tab)*1000)/10
	hyper=round(sum((tab[,"# methylated"]/tab[,"Coverage"])>=0.8)/nrow(tab)*1000)/10
	normo=100-(hypo+hyper)

sel=tab[,"Coverage"]>=5
#methyl5=round(sum(tab[sel,"# methylated"])/sum(tab[sel,"Coverage"])*1000)/10
methyl5=round(mean(tab[sel,"# methylated"]/tab[sel,"Coverage"])*1000)/10
	hypo5=round(sum((tab[sel,"# methylated"]/tab[sel,"Coverage"])<=0.2)/nrow(tab[sel,])*1000)/10
	hyper5=round(sum((tab[sel,"# methylated"]/tab[sel,"Coverage"])>=0.8)/nrow(tab[sel,])*1000)/10
	normo5=100-(hypo5+hyper5)

sel=tab[,"Coverage"]>=5 & tab[,"Coverage"]<=500
#methyl5_500=round(sum(tab[sel,"# methylated"])/sum(tab[sel,"Coverage"])*1000)/10
methyl5_500=round(mean(tab[sel,"# methylated"]/tab[sel,"Coverage"])*1000)/10
	hypo5_500=round(sum((tab[sel,"# methylated"]/tab[sel,"Coverage"])<=0.2)/nrow(tab[sel,])*1000)/10
	hyper5_500=round(sum((tab[sel,"# methylated"]/tab[sel,"Coverage"])>=0.8)/nrow(tab[sel,])*1000)/10
	normo5_500=100-(hypo5_500+hyper5_500)

sel=tab[,"Coverage"]>=10
#methyl10=round(sum(tab[sel,"# methylated"])/sum(tab[sel,"Coverage"])*1000)/10
methyl10=round(mean(tab[sel,"# methylated"]/tab[sel,"Coverage"])*1000)/10
	hypo10=round(sum((tab[sel,"# methylated"]/tab[sel,"Coverage"])<=0.2)/nrow(tab[sel,])*1000)/10
	hyper10=round(sum((tab[sel,"# methylated"]/tab[sel,"Coverage"])>=0.8)/nrow(tab[sel,])*1000)/10
	normo10=100-(hypo10+hyper10)

sel=tab[,"Coverage"]>=10 & tab[,"Coverage"]<=500
#methyl10_500=round(sum(tab[sel,"# methylated"])/sum(tab[sel,"Coverage"])*1000)/10
methyl10_500=round(mean(tab[sel,"# methylated"]/tab[sel,"Coverage"])*1000)/10
	hypo10_500=round(sum((tab[sel,"# methylated"]/tab[sel,"Coverage"])<=0.2)/nrow(tab[sel,])*1000)/10
	hyper10_500=round(sum((tab[sel,"# methylated"]/tab[sel,"Coverage"])>=0.8)/nrow(tab[sel,])*1000)/10
	normo10_500=100-(hypo10_500+hyper10_500)

sel=tab[,"Coverage"]>500
#methyl500=round(sum(tab[sel,"# methylated"])/sum(tab[sel,"Coverage"])*1000)/10
methyl500=round(mean(tab[sel,"# methylated"]/tab[sel,"Coverage"])*1000)/10
	hypo500=round(sum((tab[sel,"# methylated"]/tab[sel,"Coverage"])<=0.2)/nrow(tab[sel,])*1000)/10
	hyper500=round(sum((tab[sel,"# methylated"]/tab[sel,"Coverage"])>=0.8)/nrow(tab[sel,])*1000)/10
	normo500=100-(hypo500+hyper500)


methylation=rbind(
	       cbind("Average methylation on uniquely mapped positions","(coverage : no filter)",methyl),
	       cbind("  % hypomethylated (<=20%)=",hypo,""),
	       cbind("  % intermediate   (]20;80[%)=",normo,""),
	       cbind("  % hypermethylated (>=80%)=",hyper,""),
	       cbind("Average methylation on uniquely mapped positions","(coverage>=5)",methyl5),
	       cbind("  % hypomethylated (<=20%)=",hypo5,""),
	       cbind("  % intermediate   (]20;80[%)=",normo5,""),
	       cbind("  % hypermethylated (>=80%)=",hyper5,""),
	       cbind("Average methylation on uniquely mapped positions","(coverage in [5;500])",methyl5_500),
	       cbind("  % hypomethylated (<=20%)=",hypo5_500,""),
	       cbind("  % intermediate   (]20;80[%)=",normo5_500,""),
	       cbind("  % hypermethylated (>=80%)=",hyper5_500,""),
	       cbind("Average methylation on uniquely mapped positions","(coverage>=10)",methyl10),
	       cbind("  % hypomethylated (<=20%)=",hypo10,""),
	       cbind("  % intermediate   (]20;80[%)=",normo10,""),
	       cbind("  % hypermethylated (>=80%)=",hyper10,""),
	       cbind("Average methylation on uniquely mapped positions","(coverage in [10;500])",methyl10_500),
	       cbind("  % hypomethylated (<=20%)=",hypo10_500,""),
	       cbind("  % intermediate   (]20;80[%)=",normo10_500,""),
	       cbind("  % hypermethylated (>=80%)=",hyper10_500,""),
	       cbind("Average methylation on uniquely mapped positions","(coverage>500)",methyl500),
	       cbind("  % hypomethylated (<=20%)=",hypo500,""),
	       cbind("  % intermediate   (]20;80[%)=",normo500,""),
	       cbind("  % hypermethylated (>=80%)=",hyper500,"")
)
write.table(file=paste(dir_data,"/quality_control/",dir_name,"_methylation_summary.txt",sep=""),
	    methylation,sep="\t",quote=F,row.names=F,col.names=F
)

for (threshold in c(5,10)) {
	sel=tab[,"Coverage"]>=threshold
	meth=tab[sel,"% methylated"]
	hist(meth,nclass=60,
	     main=paste("Distribution of % methylation\nCoverage>=",threshold,sep=""),
	     xlab="% of methylated reads"
	)
	sel=tab[,"Coverage"]>=threshold & tab[,"Coverage"]<=500
	meth=tab[sel,"% methylated"]
	hist(meth,nclass=60,
	     main=paste("Distribution of % methylation\nCoverage in [",threshold,";500]",sep=""),
	     xlab="% of methylated reads"
	)
}

###############################
# Interval between covered CG #
###############################
for (threshold in c(5,10)) {
for (loop in 1:2) {
	#Distance between next position
	distance=c()
	for (chr in chromosomes) {
		if (loop==1) {
			sel=tab[,"Chromosome"]==chr & tab[,"Coverage"]>=threshold
			stitle=paste(">=",threshold,sep="")
		} else {
			sel=tab[,"Chromosome"]==chr & tab[,"Coverage"]>=threshold & tab[,"Coverage"]<=500
			stitle=paste(" in [",threshold,";500]",sep="")
		}
		positions=tab[sel,"Position"]
		if (length(positions)>1) {
			distance=c(distance,positions[2:length(positions)]-positions[1:(length(positions)-1)])
		}
	}
	if (length(distance)>1000) {
		q=quantile(distance,seq(0,1,0.05))
		pct90=q[19]
		d=distance[distance<=pct90]
		c=hist(d,breaks=50,
			main=paste("Distribution of interval between 2 CPgs\nwith coverage",stitle,sep=""),
			xlab="Distance"
		)
	
		s=summary(distance)
		names(s)=c("Minimum","1st quartile","Median","Mean","3rd quartile","Maximum")
		ymax=max(c$counts)
		for (i in 1:length(s)) {
			x=pct90*0.9
			y=ymax-(i*ymax*0.05)
			text(x,y,paste(names(s)[i],"=",s[i],sep=""),pos=2)
		}

#		res=c()
#		for 
#		barplot(height=q[1:19],xaxt="n",
#			width=1,space=0,
#			main=paste("Distance to next CpG\nCoverage>=",threshold,sep=""),
#			ylab="Distance",xlab="Quantile"
#		)
#		axis(at=1:19-0.5,labels=names(q)[1:19],side=1,las=2)
	}
}
}

dev.off()

