#!/bin/bash 

echo "#################"
echo "# EasyPipeline  #"
echo "#################"


export EASYPIPELINE_PATH=$(pwd)
export PYTHONPATH=$EASYPIPELINE_PATH:$PYTHONPATH

export PATH=$EASYPIPELINE_PATH/easypipeline/cli:$PATH