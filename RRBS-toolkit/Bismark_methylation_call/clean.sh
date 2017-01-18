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

rm -f $dir_data/trim_galore/*fastq*gz $dir_data/trim_galore/*fq*gz $dir_data/trim_galore/*fastqc.zip
if [ $? -ne 0 ]
then
    echo "Cleaning of the 'Trim galore' directory failed!"
    exit 1
fi


for sam_file in `find $dir_data/bismark -name "*.sam"`
do
	bam_file=`echo $sam_file | sed 's/sam$/bam/'`
	$SAMTOOLS_EXECUTE view -bh ${sam_file} -o ${bam_file}
	if [ $? -ne 0 ]
	then
	    echo "Compression of sam file '$sam_file' failed!"
	    exit 1
	fi
	rm -f $sam_file
	if [ $? -ne 0 ]
	then
	    echo "Deletion of .sam files failed!"
	    exit 1
	fi
	# LJO 20160428 : unmapped and ambiguous files are deleted
	rm -f  $dir_data/bismark/*_unmapped_reads*.fq
	rm -f  $dir_data/bismark/*_ambiguous_reads*.fq

done

rm -f $dir_data/extract/Non_CpG_context_*
if [ $? -ne 0 ]
then
    echo "Deletion of the extract/Non_CpG file failed!"
    exit 1
fi

#In case someneone wants to keep detail of each read ..
#gzip -f $dir_data/extract/CpG_context_*
#if [ $? -ne 0 ]
#then
#    echo "Compression of the extract/CpG file failed!"
#    exit 1
#fi
rm -f $dir_data/extract/CpG_context_*
if [ $? -ne 0 ]
then
    echo "Deletion of the extract/CpG file failed!"
    exit 1
fi

exit 0
