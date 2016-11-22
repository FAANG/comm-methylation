#!/bin/sh
#$ -l mem=10G
#$ -l h_vmem=20G


RRBS_PIPELINE_HOME=`dirname $0`
.  $RRBS_PIPELINE_HOME/../config.sh

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

