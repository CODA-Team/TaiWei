#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLOW_ROOT="${SCRIPT_DIR}"
while [[ "${FLOW_ROOT}" != "/" && ! -f "${FLOW_ROOT}/env.sh" ]]; do
  FLOW_ROOT="$(dirname "${FLOW_ROOT}")"
done
if [[ ! -f "${FLOW_ROOT}/env.sh" ]]; then
  echo "ERROR: env.sh not found for ${SCRIPT_DIR}" >&2
  exit 1
fi
source "${FLOW_ROOT}/env.sh"

export DESIGN_DIMENSION="3D"
export DESIGN_NICKNAME="aes"
export USE_FLOW="openroad"
export FLOW_VARIANT="openroad_${hbPitch}"

if [[ "${ORD_EVAL_MODE}" == "remote" ]]; then
    SSH_OPTS=()
    if [[ -n "${ORD_EVAL_SSH_OPTS:-}" ]]; then
        read -r -a SSH_OPTS <<< "${ORD_EVAL_SSH_OPTS}"
    fi
    ssh "${SSH_OPTS[@]}" -t "${ORD_EVAL_REMOTE_USER}@${ORD_EVAL_REMOTE_HOST}" "
        cd ${ORD_EVAL_REMOTE_PROJECT_DIR} || exit
        source env.sh
        export DESIGN_DIMENSION=\"${DESIGN_DIMENSION}\"
        export DESIGN_NICKNAME=\"${DESIGN_NICKNAME}\"
        export USE_FLOW=\"${USE_FLOW}\"
        export FLOW_VARIANT=\"${FLOW_VARIANT}\"
        export TECH_LEF=\"${TECH_LEF}\"
        make DESIGN_CONFIG=designs/asap7_3D/\${DESIGN_NICKNAME}/config.mk cds-final
    "
else
    make DESIGN_CONFIG=designs/asap7_3D/${DESIGN_NICKNAME}/config.mk cds-final
fi
