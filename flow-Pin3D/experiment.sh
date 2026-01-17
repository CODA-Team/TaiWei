#!/bin/bash

export DESIGN_DIMENSION="3D"
# export DESIGN_DIMENSION="3D_tiling"
export DEF_VERSION="bp_be"
export DESIGN_NAME="bp_be_top"
echo $DESIGN_DIMENSION, $DEF_VERSION, $DESIGN_NAME
export OPENROAD_EXE=$(command -v openroad)
export YOSYS_EXE=$(command -v yosys)

# make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_upper_shrink.mk do-autoflow 
# make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-cts_eval 
make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-hotspot
# make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_tiling.mk do-hotspot