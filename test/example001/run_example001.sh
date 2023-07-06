#!/bin/sh -f

export TMP_PATH=$(pwd) # get current path to return here after this script 
cd $EASYPIPELINE_PATH/test/example001 # move to the example directory and prepare 

run_pipeline.py \
	--name easypipeline \
	--param input/parameter/input_parameter.yaml \
	--column input/parameter/def_columns.yaml \
	--indir input/data \
	--outdir output 

cd $TMP_PATH


