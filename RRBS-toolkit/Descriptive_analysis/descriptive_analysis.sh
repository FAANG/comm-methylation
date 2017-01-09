#SGE parameters
#!/bin/sh
#$ -l mem=20G
#$ -l h_vmem=80G
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
	SCRIPT_DIR=`dirname $0`
else
	#Use RRBS_HOME as defined in environment variable
	SCRIPT_DIR="$RRBS_HOME/Descriptive_analysis"
fi
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

