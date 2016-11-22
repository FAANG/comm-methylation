SCRIPT_DIR=`dirname $0`
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

