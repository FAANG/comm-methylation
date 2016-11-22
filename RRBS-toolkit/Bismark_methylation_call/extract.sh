#!/bin/sh
#$ -l mem=10G
#$ -l h_vmem=20G

RRBS_PIPELINE_HOME=`dirname $0`
.  $RRBS_PIPELINE_HOME/../config.sh

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

R2=`find $dir_data/trim_galore -name "*R2_val_2.fq*"`

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
