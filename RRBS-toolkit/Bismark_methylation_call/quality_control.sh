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
dir="$(basename $dir_data)"


work_dir_qual="./$dir_data/quality_control"

(
echo "Quality control R script starting ..."
if [ ! -d  $work_dir_qual ]
then
    mkdir $work_dir_qual
    chmod 775 $work_dir_qual
    if [ $? -ne 0 ]
    then
        echo "Quality control output directory impossible to create"
        exit 1
    fi
fi

$R_EXECUTE CMD BATCH  --no-restore --no-save "--args $dir_data" $RRBS_PIPELINE_HOME/quality_control.R \
	     $work_dir_qual/quality_control.Rout
if [ $? -ne 0 ]
then
    echo "Quality control script failed!"
    exit 1
fi
echo "Done !"

) 1> $dir_data/quality_control.log 2>&1
if [ $? -ne 0 ]
then
    # process error exit
    exit 1
fi

(
#Extract summary report
echo "" 
echo "+------------------+" 
echo "| Coverage stats   |"
echo "+------------------+"
cat "$dir_data/quality_control/${dir}_coverage_summary.txt"

echo "" 
echo "+---------------------+" 
echo "| Methylation stats   |"
echo "+---------------------+"
cat "$dir_data/quality_control/${dir}_methylation_summary.txt"
)>> $dir_data/${dir}_summary_report.txt


