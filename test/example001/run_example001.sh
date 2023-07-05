#!/bin/sh -f

export TMP_PATH=$(pwd) # get current path to return here after this script 

cd $EASYPIPELINE_PATH/test/example001 # move to the example directory and prepare 

run_pipeline.py \
	-n easypipeline \
	-p input/parameter/input_parameter.yaml \
	-c input/parameter/def_columns.yaml \
	-i input/data \
	-o output 

cd $TMP_PATH


