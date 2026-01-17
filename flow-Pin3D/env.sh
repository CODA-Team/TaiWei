#!/usr/bin/env bash

function __setpaths() {
  DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
  if [[ -z "${FLOW_ENV_QUIET:-}" ]]; then
    echo "Setting FLOW_HOME to $DIR"
  fi
  export FLOW_HOME="$DIR"
}
__setpaths


# ------------------------------------------------------------------------------
# Toolchain paths (override in your shell if needed) (OpenROAD-flow-scripts)
# ------------------------------------------------------------------------------
export WORK_DIR="${WORK_DIR:-$(pwd)}"  # Please update your working directory
export ORFS_DIR="${ORFS_DIR:-$(pwd)/OpenROAD-flow-scripts}"  # Please update your OpenROAD-flow-scripts directory
export OPENROAD_EXE="${OPENROAD_EXE:-${ORFS_DIR}/tools/install/OpenROAD/bin/openroad}"
export YOSYS_EXE="${YOSYS_EXE:-${ORFS_DIR}/tools/install/yosys/bin/yosys}"
export STA_EXE="${STA_EXE:-${ORFS_DIR}/tools/install/OpenROAD/bin/sta}"
export NUM_CORES="${NUM_CORES:-16}"
