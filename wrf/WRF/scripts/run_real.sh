#!/usr/bin/env bash
# ==============================================================================
# SAMEER — Real.exe Vertical Interpolation and IC/BC Generator
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRF_RUN_DIR="$(dirname "$SCRIPT_DIR")/run"
cd "$WRF_RUN_DIR"

CORES="${1:-8}"
echo "Running real.exe with $CORES MPI tasks in $WRF_RUN_DIR"

if [ ! -f "real.exe" ]; then
    echo "ERROR: real.exe binary not found in $WRF_RUN_DIR"
    exit 1
fi

mpirun -np "$CORES" ./real.exe > real.log 2>&1
echo "real.exe completed. Output files: wrfinput_d01, wrfinput_d02, wrfinput_d03, wrfbdy_d01"
