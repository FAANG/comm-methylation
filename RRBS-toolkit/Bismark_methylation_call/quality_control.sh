#!/bin/sh
#$ -l mem=10G
#$ -l h_vmem=20G

RRBS_PIPELINE_HOME=`dirname $0`
.  $RRBS_PIPELINE_HOME/../config.sh

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


