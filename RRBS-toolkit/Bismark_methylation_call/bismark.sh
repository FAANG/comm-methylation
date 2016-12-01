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
dir_genome=$2

dir_data_basename=`basename "$dir_data"`

work_dir_bis="$dir_data/bismark"

logFile="$dir_data/bismark.log"
(
if [ ! -d  $work_dir_bis ]
then
    mkdir $work_dir_bis
    chmod 775 $work_dir_bis
    if [ $? -ne 0 ]
    then
        echo "Bismark output directory impossible to create"
        exit 1
    fi
fi


R2=`find $dir_data/trim_galore -name "*R2_val_2.fq*"`
if [  -f "$R2" ]

	then
	R1=`find $dir_data/trim_galore -name "*R1_val_1.fq*"`
	$BISMARK_HOME/bismark --unmapped --ambiguous \
	 $dir_genome \
	-1 $R1 -2 $R2\
	--path_to_bowtie $BOWTIE_HOME \
	--output_dir $work_dir_bis



else 
	R1=`find $dir_data/trim_galore -name "*R1_trimmed.fq*"`
	$BISMARK_HOME/bismark --unmapped --ambiguous \
	 $dir_genome \
	$R1 \
	--path_to_bowtie $BOWTIE_HOME \
	--output_dir $work_dir_bis

fi

if [ $? -ne 0 ]
then
    echo "Problem during bismark run"
    exit 1
fi

exit $?

) 1> $logFile 2>&1
    
if [ $? -ne 0 ]
then
    #Former process error output
    exit 1
fi

(
#Extract summary report
echo "" 
echo "+------------------+" 
echo "| Bismark step     |"
echo "+------------------+"
$PYTHON_EXECUTE $RRBS_PIPELINE_HOME/get_bismark_report.py $logFile
)>> $dir_data/summary_report.txt

