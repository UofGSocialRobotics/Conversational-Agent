#!/usr/bin/env bash
export PYTHONPATH=~/Desktop/Conversational_Agent/server_side
export PYTHONHASHSEED=1
python ${PYTHONPATH}/food/food_diagnostic_analysis.py $*
