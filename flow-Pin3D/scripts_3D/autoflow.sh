#!/bin/bash

export DESIGN_DIMENSION=$1
export DEF_VERSION=$2
export DESIGN_NAME=$3
echo $DESIGN_DIMENSION, $DEF_VERSION, $DESIGN_NAME
export OPENROAD_EXE=$(command -v openroad)
export YOSYS_EXE=$(command -v yosys)
if [ "$DESIGN_DIMENSION" = "3D" ]
then
    cp ../../Place-3D/install/results/${DEF_VERSION}_${DESIGN_DIMENSION}/${DEF_VERSION}_${DESIGN_DIMENSION}.gp.def designs/nangate45_3D/${DESIGN_NAME}/
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_upper_shrink.mk do-autoflow 
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-cts_eval 
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-hotspot

elif [ "$DESIGN_DIMENSION" = "3D_tiling" ]
then
    cp ../../Place-3D/install/results/${DEF_VERSION}_${DESIGN_DIMENSION}/${DEF_VERSION}_${DESIGN_DIMENSION}.gp.def designs/nangate45_3D/${DESIGN_NAME}/
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_tiling_upper_shrink.mk do-autoflow 
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_tiling.mk do-cts_eval 
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_tiling.mk do-hotspot 

elif [ "$DESIGN_DIMENSION" = "true_3D" ]
then
    cp ../../Place-3D/install/results/${DEF_VERSION}_${DESIGN_DIMENSION}/${DEF_VERSION}_${DESIGN_DIMENSION}.gp.def designs/nangate45_3D/${DESIGN_NAME}/
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_true_3D_upper_shrink.mk do-autoflow 
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_true_3D.mk do-cts_eval 
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_true_3D.mk do-hotspot 

elif [ "$DESIGN_DIMENSION" = "2D" ] 
then
    cp ../../Place-3D/install/results/${DEF_VERSION}_${DESIGN_DIMENSION}/${DEF_VERSION}_${DESIGN_DIMENSION}.gp.def designs/nangate45/${DESIGN_NAME}/
    make DESIGN_CONFIG=designs/nangate45/${DESIGN_NAME}/config_2d_dmp.mk do-def_eval
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-hotspot_2D

elif [ "$DESIGN_DIMENSION" = "2D_mp" ]
then
    cp ../../Place-3D/install/results/${DEF_VERSION}_${DESIGN_DIMENSION}/${DEF_VERSION}_${DESIGN_DIMENSION}.gp.def designs/nangate45/${DESIGN_NAME}/
    make DESIGN_CONFIG=designs/nangate45/${DESIGN_NAME}/config_mp.mk do-def_eval
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-hotspot_2D

elif [ "$DESIGN_DIMENSION" = "Pin3DFlow" ]
then
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config2d.mk do-pin-3d-flow-2dpre
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-pin-3d-flow-pre
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-pin-3d-flow-place-init
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_bottom_shrink.mk do-pin-3d-flow-place-upper
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_upper_shrink.mk do-pin-3d-flow-place-bottom
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config_upper_shrink.mk do-autoflow 
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-cts_eval 
    make DESIGN_CONFIG=designs/nangate45_3D/${DESIGN_NAME}/config.mk do-hotspot
else
    echo "unknown running mode, exit"
fi
python3 scripts_3D/get_metrics.py
echo "job done, exit"