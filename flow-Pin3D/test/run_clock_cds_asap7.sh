#!/bin/bash

# Define the base directories
LOG_DIR="run_logs/asap7_3D/aes/cds_clock"
SCRIPT_DIR="test/asap7_3D/aes/cds_clock"

# Create the log directory
mkdir -p "$LOG_DIR"

# Generate clock periods from 1.0 down to 0.5 with a step of 0.05
clocks=()
for i in $(seq 480 -20 300); do
    clocks+=("$i")
done

# Loop through each pitch and run in background
for clk in "${clocks[@]}"; do
    (
        echo "Start: ${SCRIPT_DIR}/run.sh with CLK_PERIOD=$clk"
        export CLK_PERIOD=$clk
        bash "${SCRIPT_DIR}/run.sh" > "${LOG_DIR}/run_${clk}.log" 2>&1
        echo "Done: ${clk}.sh"
    ) &
done

# Wait for all background jobs to finish
wait
echo "All jobs completed."