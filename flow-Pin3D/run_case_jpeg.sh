#!/bin/bash
bash ./env.sh

export DESIGN_DIMENSION="3D"
export DEF_VERSION="jpeg"
export DESIGN_NAME="jpeg" 
make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config2d.mk do-pin-3d-flow-2dpre
make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-pin-3d-flow-pre
make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_both_shrink.mk do-pin-3d-flow-place-init
iteration=1
for ((i=1;i<=iteration;i++))
do
    echo "Iteration: $i"
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_bottom_shrink.mk do-pin-3d-flow-place-upper
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_upper_shrink.mk do-pin-3d-flow-place-bottom
done
cp -r results/nangate45_3D/${DESIGN_NAME}/${DESIGN_DIMENSION}/${DEF_VERSION}_${DESIGN_DIMENSION}.gp.def designs/nangate45_3D/${DESIGN_NAME}/${DEF_VERSION}_${DESIGN_DIMENSION}.gp.def
make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_upper_shrink.mk do-autoflow 
make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-cts_eval 
make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-hotspot
