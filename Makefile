# The official-2d branch runs the upstream ORFS flow by default.
.DEFAULT_GOAL := all

ORFS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))ORFS-Research
export FLOW_HOME := $(ORFS_DIR)/flow
export OPENROAD_EXE := $(ORFS_DIR)/tools/install/OpenROAD/bin/openroad
export OPENSTA_EXE := $(ORFS_DIR)/tools/install/OpenROAD/bin/sta
export YOSYS_EXE := $(ORFS_DIR)/tools/install/yosys/bin/yosys

.PHONY: all synth floorplan place cts route finish gui_final
all synth floorplan place cts route finish gui_final:
	+$(MAKE) -C "$(FLOW_HOME)" $@
