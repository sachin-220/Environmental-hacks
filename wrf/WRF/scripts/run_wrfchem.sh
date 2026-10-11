#!/usr/bin/env bash
# ==============================================================================
# SAMEER — WRF-Chem Coupled Meteorology-Chemistry Numerical Solver
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRF_RUN_DIR="$(dirname "$SCRIPT_DIR")/run"
cd "$WRF_RUN_DIR"

CORES="${1:-16}"
echo "Launching WRF-Chem numerical solver with $CORES MPI tasks..."

if [ ! -f "wrf.exe" ]; then
    echo "ERROR: wrf.exe binary not found in $WRF_RUN_DIR"
    exit 1
fi

mpirun -np "$CORES" ./wrf.exe > wrf.log 2>&1
echo "WRF-Chem coupled numerical simulation complete. Outputs in wrfout_d01_*, wrfout_d02_*, wrfout_d03_*"
