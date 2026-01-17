#!/bin/bash

# Define the base directories
LOG_DIR="run_logs/asap7_nangate45_3D/jpeg/ord_pitch"
SCRIPT_DIR="test/asap7_nangate45_3D/jpeg/ord_pitch"

# Create the log directory
mkdir -p "$LOG_DIR"

# List of pitch suffixes to run
# pitches=("0p2" "0p4" "0p6" "0p8" "1" "1p2" "1p4" "1p6")
pitches=("1" "1p6")
# Loop through each pitch and run in background
for p in "${pitches[@]}"; do
    (
        echo "Start: ${SCRIPT_DIR}/run_${p}.sh"
        export hbPitch="hbPitch_${p}"
        bash "${SCRIPT_DIR}/run.sh" > "${LOG_DIR}/run_${p}.tmp.log" 2>&1
        mv "${LOG_DIR}/run_${p}.tmp.log" "${LOG_DIR}/run_${p}.log"
        echo "Done: run.sh"
    ) &
done

# Wait for all background jobs to finish
wait
echo "All jobs completed."
