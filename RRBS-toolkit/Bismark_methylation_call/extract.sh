#!/bin/sh
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
dir_data_basename="$(basename $dir_data)"

work_dir_ext="$dir_data/extract"


(

if [ ! -d  $work_dir_ext ]
then
    mkdir $work_dir_ext
    chmod 775 $work_dir_ext
    if [ $? -ne 0 ]
    then
        echo "methylation extract output directory impossible to create"
        exit 1
    fi
fi

#Depending on bismark version, output is either SAM or BAM
fileToExtract=`find $dir_data/bismark -name "*.[bs]am"`


if [ "$fileToExtract" = "" ]

then
	echo $dir_data_basename
	echo "Neither BAM nor SAM files found while trying to extract methylation data."
	exit 1
fi

echo "bismark extraction running (1) ..."

$BISMARK_HOME/bismark_methylation_extractor \
	--no_overlap --comprehensive --merge_non_CpG \
        $fileToExtract -o $work_dir_ext
if [ $? -ne 0 ]
then
    echo "bismark extraction failed (1)"
    exit 1
fi
echo "Done !"

echo "bismark extraction running (2) ..."
$PYTHON_EXECUTE $RRBS_PIPELINE_HOME/parse_extract.py $dir_data 
if [ $? -ne 0 ]
then
    echo "bismark extraction failed (2)"
    exit 1
fi
echo "Done !"


#R1<->R2 distance extraction

R2=`find $dir_data/trim_galore -name "*R2_val_2.fq*" | wc -l`

if [ $R2 -eq 1 ]

	then

	echo "R1<->R2 distance extraction running ..."
	$PYTHON_EXECUTE $RRBS_PIPELINE_HOME/extract_distance_R1R2.py $dir_data $fileToExtract
	if [ $? -ne 0 ]
	then
    	echo "R1<->R2 distance extraction failed (2)"
    	exit 1
	fi
	echo "Done !"

exit 0

fi


) 1> $dir_data/extract.log 2>&1

if [ $? -ne 0 ]
then
    #Former process error output
    exit 1
fi
