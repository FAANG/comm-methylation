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
	--path_to_cutadapt $CUTADAPT_EXECUTE --fastqc --paired --rrbs --non_directional --trim1 \
	"$file_R1" "$file_R2" \
	--output_dir $work_dir

else
		echo "Launching trim_galore on "$file_R1" file ..."
	$TRIMGALORE_EXECUTE \
	--path_to_cutadapt $CUTADAPT_EXECUTE --fastqc --rrbs --non_directional --trim1 \
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
