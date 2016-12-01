#!/bin/sh
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
	SCRIPT_DIR="$RRBS_HOME/Annotation"
fi
. $SCRIPT_DIR/../config.sh

echo "-------------------------------------------"
echo "Testing annotation toolkit ..."
echo "-------------------------------------------"
IFS_BAK=$IFS
IFS="
"
first_line=1

cd $RRBS_HOME/Annotation
mkdir temp_tests

nb_KO=0
for line in `cat test_set/test_table.txt`
do
	IFS=${IFS_BAK}
	if [ $first_line -ne 1 ]
	then
		config_file=`echo $line | sed 's/[ \t].*$//'`
		config_file="test_set/$config_file"
		output_file=`grep "output_file" $config_file  | sed 's/.*[ \t]//'`
		test_label=`echo $line | sed 's/.*Testing/Testing/'`
		expected_file=`echo $output_file | sed 's/temp_tests/test_set\/expected_results/'`
		echo "$test_label ..."

		$PYTHON_EXECUTE $RRBS_HOME/Annotation/annotk/annotk.py $config_file 1>/dev/null
		if [ $? -eq 1 ]
		then
			echo "    Failed !"
		else
			diff $output_file $expected_file 1>/dev/null
			ret_diff=$?
			if [ $ret_diff -eq 0 ]
			then
				echo "    OK"
			elif [ $ret_diff -eq 1 ]
			then
				echo "    KO !!!! Differences exists with expected result"
				nb_KO=1
			else
				echo "    KO !!!! Comparison with expected results failed"
				nb_KO=1
			fi
		fi
		
	fi
	first_line=0
done

rm -rf temp_tests

echo "-------------------------------------------"
if [ $nb_KO -ne 0 ]
then
	echo "Conclusion : Some tests failed !"
else
	echo "Conclusion : All tests passed !"
fi
