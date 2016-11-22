SCRIPT_DIR=`dirname $0`
. $SCRIPT_DIR/../config.sh

$PYTHON_EXECUTE $RRBS_HOME/Annotation/annotk/annotk.py annotk_config_example.txt
