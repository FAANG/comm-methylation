#!/bin/sh
#$ -l mem=10G
#$ -l h_vmem=20G

RRBS_PIPELINE_HOME=`dirname $0`
.  $RRBS_PIPELINE_HOME/../config.sh

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
