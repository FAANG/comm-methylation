#SGE parameters
#!/bin/sh
#$ -l mem=20G
#$ -l h_vmem=80G

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

logFile="$outputDir/descriptive_analysis.$$.log"

$R_EXECUTE CMD BATCH --no-restore --no-save "--args $configFile $logFile" $SCRIPT_DIR/descriptive_analysis.R $outputDir/descriptive_analysis.$$.Rout

