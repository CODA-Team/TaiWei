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
# Toolchain paths (override in your shell if needed)
# ------------------------------------------------------------------------------
export OPENROAD_EXE="${OPENROAD_EXE:-/scripts/ORFS-Research/tools/install/OpenROAD/bin/openroad}"
export YOSYS_EXE="${YOSYS_EXE:-/scripts/ORFS-Research/tools/install/yosys/bin/yosys}"
export STA_EXE="${STA_EXE:-/scripts/ORFS-Research/tools/install/OpenROAD/bin/sta}"
export NUM_CORES="${NUM_CORES:-16}"
export OPENROAD_CMD_DOCKER="${OPENROAD_CMD_DOCKER:-${OPENROAD_EXE} -threads ${NUM_CORES}}"

# ------------------------------------------------------------------------------
# Cadence flow: TritonPart partitioning via OpenROAD (local or docker)
# ------------------------------------------------------------------------------
# CDS_PARTITION_MODE: "docker" (default) or "local"
export CDS_PARTITION_MODE="${CDS_PARTITION_MODE:-docker}"
if [[ "${CDS_PARTITION_MODE}" == "docker" ]]; then
  export CDS_USE_OPENROADDOCKER=1
  export CDS_PARTITION_TARGET="cds-docker-partition"
else
  export CDS_USE_OPENROADDOCKER=0
  export CDS_PARTITION_TARGET="cds-tier-partition"
fi

# Docker settings (used when CDS_PARTITION_MODE=docker)
export DOCKER="${DOCKER:-docker}"
export CONTAINER="${CONTAINER:-orfs_zhiyu}"
export CONTAINER_USER="${CONTAINER_USER:-zhiyuzheng}"
export INNER_DIR="${INNER_DIR:-/scripts/ORFS-Research/flow-Pin3D}"

# ------------------------------------------------------------------------------
# OpenROAD flow eval (cds-final) location
# ------------------------------------------------------------------------------
# If Innovus is only available on another server, set ORD_EVAL_MODE=remote.
# When remote, run_experiments.py will SSH to run eval.sh (which calls cds-final).
export ORD_EVAL_MODE=remote
export ORD_EVAL_REMOTE_HOST=hnode35
export ORD_EVAL_REMOTE_PROJECT_DIR=/export/home/zhiyuzheng/Projects/3DIC/scripts/ORFS-Research/flow-Pin3D

export ORD_EVAL_MODE="${ORD_EVAL_MODE:-local}" # local | remote
export ORD_EVAL_REMOTE_USER="${ORD_EVAL_REMOTE_USER:-${USER:-zhiyuzheng}}"
export ORD_EVAL_REMOTE_HOST="${ORD_EVAL_REMOTE_HOST:-${HOSTNAME:-localhost}}"
export ORD_EVAL_REMOTE_PROJECT_DIR="${ORD_EVAL_REMOTE_PROJECT_DIR:-${FLOW_HOME}}"
export ORD_EVAL_SSH_OPTS="${ORD_EVAL_SSH_OPTS:-}"