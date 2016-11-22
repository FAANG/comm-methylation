#!/bin/sh
#$ -l mem=10G
#$ -l h_vmem=20G

RRBS_PIPELINE_HOME=`dirname $0`
.  $RRBS_PIPELINE_HOME/../config.sh


# arguments
dir_data=$1
file_R1=$2
file_R2=$3

work_dir="$dir_data/trim_galore"

(
if [ ! -d  $work_dir ]
then
    mkdir $work_dir
    chmod 775 $work_dir
    if [ $? -ne 0 ]
    then
        echo "Trim galore output directory impossible to create"
        exit 1
    fi
fi


####################################################################
#Trim_galore execution
####################################################################

if [ "$file_R2" != "" ]
	then
		echo "Launching trim_galore on $file_R1 and $file_R2 files ..."
		$TRIMGALORE_EXECUTE \
	--fastqc --paired --rrbs --non_directional --trim1 \
	"$file_R1" "$file_R2" \
	--output_dir $work_dir

else
		echo "Launching trim_galore on "$file_R1" file ..."
	$TRIMGALORE_EXECUTE \
	--fastqc --rrbs --non_directional --trim1 \
	"$file_R1" \
	--output_dir $work_dir

fi



if [ $? -ne 0 ]
then
    echo "Problem during trim galore run"
    exit 1
fi

) 1> $dir_data/trim_galore.log 2>&1

if [ $? -ne 0 ]
then
    # Former process error output
    exit 1
fi

(
#Extract summary report
echo "" 
echo "+------------------+" 
echo "| Trim Galore step |"
echo "+------------------+"
awk '
        /RUN STATISTICS FOR INPUT FILE:/,/^$/ {print}
	/Number of sequence pairs removed because at least one read was shorter than the length cutoff/ {print;}
        /RRBS reads trimmed by 2 bp at the start when read started with CAA / {
                line=$0;
                CAA=line;
                sub(/RRBS reads trimmed .* with CAA ./,"",CAA);
                sub(/[)].*$/,"",CAA)
                #printf("CAA=%s\n",CAA)
                CGA=line;
                sub(/RRBS reads trimmed .* or CGA ./,"",CGA);
                sub(/[)].*$/,"",CGA)
                #printf("CGA=%s\n",CGA)
		if (CAA+CGA!=0) {
			convertBisulfite=100-int((CGA/(CAA+CGA))*1000)/10
		} else {
			convertBisulfite=""
		}
	}

	END {
		printf("\nBisulfite conversion rate:\t%s%\n",convertBisulfite);
	}

' $dir_data/trim_galore.log
echo "" 
) >> $dir_data/summary_report.txt

exit 0
