#!/bin/sh
#$ -l mem=10G
#$ -l h_vmem=20G


RRBS_PIPELINE_HOME=`dirname $0`
.  $RRBS_PIPELINE_HOME/../config.sh


### Tests if genome directory is present

genome_dir=$1

if [ "$1" == "" ]; 
then
    echo "No genome directory specified in argument"
    echo "Usage : ./bismark_genome_preparation.sh <pathname to the directory where genome fasta files are located>"
    exit 1
fi


if [ ! -d "$genome_dir" ]
then
	echo "Directory '$genome_dir' do not exist"
	exit 1
fi

(

$BISMARK_HOME/bismark_genome_preparation \
	--path_to_bowtie $BOWTIE_HOME \
	$genome_dir

if [ $? -ne 0 ]
then
    echo "Problem during genome preparation run"
    exit 1
fi

exit $?

) 1> $genome_dir/bismark_genome_preparation.log 2>&1

exit $?


