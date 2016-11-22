#!/bin/sh
#$ -l mem=10G
#$ -l h_vmem=20G

SCRIPT_DIR=`dirname $0`
. $SCRIPT_DIR/../config.sh 

configFile=$1
if [ ! -f "$configFile" ]
then
	tput clear
	echo "file '$configFile' does not exists."
	echo ""
	cat $SCRIPT_DIR/readme.txt
	exit 1
fi

#Force conversion dos -> unix (Cf. http://koenaerts.ca/dos2unix-equivalent)
tmpFile="${configFile}.tmp123"
cat $configFile | tr -d '\015' > $tmpFile
mv $tmpFile $configFile

outputDir=`grep "output_dir" $configFile | sed 's/^#output_dir[ \t]*//'`
if [ "$outputDir" = "" ]
then
	outputDir="."
fi
WORK="$outputDir/tmp"
if [ ! -d "$WORK" ]
then
	mkdir $WORK
fi

PID=$$

logFile="$outputDir/get_methylation_differences.${PID}.log"

statistical_method=`grep "^#stat_method" $configFile | tr "[:lower:]" "[:upper:]" | sed 's/^.*\t//'`
DMR_only=`grep "^#DMC_file" $configFile | wc -l `

if [ $DMR_only -eq 0 -a "$statistical_method" != "" ]
then
	$PYTHON_EXECUTE $SCRIPT_DIR/rename_scaffolds.py 1 $configFile $logFile $WORK $PID
	if [ $? -ne 0 ]
	then
		echo "L'etape rename_scaffolds.pl (1) a echoue" >> $logFile
		exit 1
	fi

	if [ "$statistical_method" = "METHYLKIT" ]
	then
		$R_EXECUTE CMD BATCH --no-restore --no-save "--args $configFile $logFile $WORK $PID" $SCRIPT_DIR/get_diff_methylKit.R $WORK/get_diff_methylKit.$PID.Rout
	elif [ "$statistical_method" = "METHYLSIG" ]
	then
		$R_EXECUTE CMD BATCH --no-restore --no-save "--args $configFile $logFile $WORK $PID" $SCRIPT_DIR/get_diff_methylSig.R $WORK/get_diff_methylSig.$PID.Rout
	else
		echo "Unexpected value for 'stat_method' parameter : Recieved '$statistical_method'. Attempted either 'methylSig' or 'methylKit'."
		exit 1
	fi
	
	$PYTHON_EXECUTE $SCRIPT_DIR/rename_scaffolds.py 2 $configFile $logFile $WORK $PID
	if [ $? -ne 0 ]
	then
		echo "L'etape rename_scaffolds.pl (2) a echoue" >> $logFile
		exit 1
	fi

	$PYTHON_EXECUTE $SCRIPT_DIR/get_bed_from_methylDiff.py $configFile $logFile
	if [ $? -ne 0 ]
	then
		echo "L'etape get_bed_from_methylKit.pl a echoue" >> $logFile
		exit 1
	fi
fi

if [ $DMR_only -eq 0 ]
then
	$PYTHON_EXECUTE $SCRIPT_DIR/get_obvious_DMC.py $configFile $logFile
	if [ $? -ne 0 ]
	then
		echo "L'etape get_obvious_DMC.pl a echoue" >> $logFile
		exit 1
	fi
fi

if [ $DMR_only -eq 0 -a "$statistical_method" != "" ]
then
	$PYTHON_EXECUTE $SCRIPT_DIR/merge_DMCs.py $configFile $logFile
	if [ $? -ne 0 ]
	then
		echo "L'etape merge_DMCs.pl a echoue" >> $logFile
		exit 1
	fi
fi

$PYTHON_EXECUTE $SCRIPT_DIR/get_DMRs.py $configFile $logFile
if [ $? -ne 0 ]
then
	echo "L'etape get_DMRs.pl a echoue" >> $logFile
	exit 1
fi

rm -rf $WORK

