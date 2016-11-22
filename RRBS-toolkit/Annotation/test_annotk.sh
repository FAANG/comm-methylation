#!/bin/sh

SCRIPT_DIR=`dirname $0`
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
