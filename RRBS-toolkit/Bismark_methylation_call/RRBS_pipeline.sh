#!/bin/sh
#Parameters for SGE submission:
#$ -e log/RRBS_pipeline_$JOB_ID.err
#$ -o log/RRBS_pipeline_$JOB_ID.out
#$ -l mem=10G
#$ -l h_vmem=20G
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

if [ "$RRBS_HOME" = "" ]
then
	#Try to find RRBS_HOME according to the way the script is launched
	RRBS_PIPELINE_HOME=`dirname $0`
else
	#Use RRBS_HOME as defined in environment variable
	RRBS_PIPELINE_HOME="$RRBS_HOME/Bismark_methylation_call"
fi
. $RRBS_PIPELINE_HOME/../config.sh

dir_data=$1
dir_genome=$2


# No slash should be added at the end of the sample directory name
dir_data=`echo $dir_data | sed 's/\/$//g'`

if [ "$dir_data" = ""  -o "$dir_genome" = "" ]
then
	echo "Usage : $0 <sample_directory> <genome_directory>"
	echo "        <sample_directory> : directory containing a fastq directory where fastq file(s) are stored"
	echo "        <genome_directory> : directory where genome fasta file have been prepared"
	exit 1
fi




# check for the presence of the dir_data directory and the dir_data/fastq directory 

if [ ! -d "$dir_data/fastq" ]
then
    echo "No directory for the dir_data : $dir_data"
    exit 1
fi


# check for the presence of the bisulfite genome 

if [ ! -d "$dir_genome/Bisulfite_Genome" ]
then
	echo "There isn't any genome bisulfite preparation in '$dir_genome'";
	exit 1;
fi



# check for the presence of the fastq files

file_number=`find $dir_data/fastq -name "*.fastq*" | wc -l`

if [ $file_number -eq 1 ]
then 
	#echo "Single end"
	manip_type=""
	R1=`find $dir_data/fastq -name "*.fastq*" `
	found1=$(echo $R1 | grep -E '.gz(ip)?$')

		if [ ! "$found1" ]
		then
     			gzip $R1
		fi
	R1=`find $dir_data/fastq -name "*.fastq*" `
	R2=""

elif [ $file_number -eq 2 ]
then
	#echo "Paired end"
	manip_type="--paired"

	# test for the presence of a R1 and a R2 file, if they have the same name and if they are zipped

	# relative path of the file
	R1=`find $dir_data/fastq -name "*R1.fastq*" `

	nom_fich_R1=`basename $R1 | sed 's/\(.*\)_R1.fastq/\1/'`

	# relative path of the file
	R2=`find $dir_data/fastq -name "*R2.fastq*"`
	
	nom_fich_R2=`basename $R2 | sed 's/\(.*\)_R2.fastq/\1/'`

	if [ "$nom_fich_R1" = "$nom_fich_R2" ]
	then
			found1=$(echo $R1 | grep -E '.gz(ip)?$')

				if [ ! "$found1" ]
				then
   			  		  gzip $R1
				fi

			found2=$(echo $R2 | grep -E '.gz(ip)?$')

				if [ ! "$found2" ]
				then
   			  		  gzip $R2
				fi
			R1=`find $dir_data/fastq -name "*R1.fastq*" `
			R2=`find $dir_data/fastq -name "*R2.fastq*"`

	else
		echo "Files R1 & R2 are not matching :"
		echo "R1= $R1"
		echo "R2= $R2"
		exit 1
        fi

else
	echo "incorrect number of fastq files"
	exit 1

fi

(
rm -f $dir_data/summary_report.txt


#trim galore run
$RRBS_PIPELINE_HOME/trim_galore.sh $dir_data $R1 $R2

if [ $? -ne 0 ]
then
    echo "Trim galore failed !!!"
    exit 1
else
    echo "Trim galore successful"
fi


# bismark run
$RRBS_PIPELINE_HOME/bismark.sh $dir_data $dir_genome 

if [ $? -ne 0 ]
then
    echo "Bismark failed !!!"
    exit 1
else
    echo "Bismark successful"
fi

# bismark methylation extractor run
$RRBS_PIPELINE_HOME/extract.sh $dir_data

if [ $? -ne 0 ]
then
    echo "MethExtract failed !!!"
    exit 1
else
    echo "MethExtract successful"
fi

$RRBS_PIPELINE_HOME/quality_control.sh $dir_data

if [ $? -ne 0 ]
then
    echo "Quality control failed !!!"
    exit 1
else
    echo "Quality control successful"
fi

# Directories cleaning
$RRBS_PIPELINE_HOME/clean.sh $dir_data
if [ $? -ne 0 ]
then
    echo "Cleaning failed !!!"
    exit 1
else
    echo "Cleaning successful"
fi

) 1> $dir_data/RRBS_pipeline.log 2>&1
