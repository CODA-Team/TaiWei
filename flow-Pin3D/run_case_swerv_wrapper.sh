#!/bin/bash
export DESIGN_DIMENSION="3D"
export DEF_VERSION="swerv_wrapper"
export DESIGN_NAME="swerv_wrapper" 
# make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config2d.mk do-pin-3d-flow-2dpre
# make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-pin-3d-flow-pre
# make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-pin-3d-flow-place-init
make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_bottom_shrink.mk do-pin-3d-flow-place-upper
make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_upper_shrink.mk do-pin-3d-flow-place-bottom
cp -r results/nangate45_3D/${DESIGN_NAME}/${DESIGN_DIMENSION}/${DEF_VERSION}_${DESIGN_DIMENSION}_bottom_out.gp.def designs/nangate45_3D/${DESIGN_NAME}/${DEF_VERSION}_${DESIGN_DIMENSION}.gp.def
make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_upper_shrink.mk do-autoflow 
make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-cts_eval 
make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-hotspot
