#!/bin/sh
#$ -l mem=10G
#$ -l h_vmem=20G
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


