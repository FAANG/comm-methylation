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

if [ "$RRBS_HOME" = "" ]
then
	#Try to find RRBS_HOME according to the way the script is launched
	SCRIPT_DIR=`dirname $0`
else
	#Use RRBS_HOME as defined in environment variable
	SCRIPT_DIR="$RRBS_HOME/Annotation"
fi
. $SCRIPT_DIR/../config.sh

if [ "$1" == "" ]
then
	echo "usage : $SCRIPT_DIR/annotate.sh <pathname to your annotation config file>"
	exit 1
fi

if [ ! -f "$1" ]
then
	echo "'$1' is not a configuration file"
	echo "usage : $SCRIPT_DIR/annotate.sh <pathname to your annotation config file>"
	exit 1
fi

$PYTHON_EXECUTE $RRBS_HOME/Annotation/annotk/annotk.py annotk_config_example.txt
exit $?

