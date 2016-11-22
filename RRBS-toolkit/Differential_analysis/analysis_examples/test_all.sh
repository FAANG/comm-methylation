#!/bin/sh
echo "Cleaning output directories ..."
for dir in out_DMR_only out_methylKit out_methylSig out_nostats
do
	rm -rf $dir
	mkdir $dir
done

SCRIPT_DIR=..

for conf in DMCs_config_methylKit.txt DMCs_config_methylSig.txt DMCs_config_nostat.txt DMCs_config_DMRonly.txt
do
	echo "Treating $conf ..."
	sh $SCRIPT_DIR/get_methylation_differences.sh $conf
	if [ $?  -ne 0 ]
	then
		echo "Failed !"
	fi
done
