#!/usr/bin/env bash
# ==============================================================================
# SAMEER — WPS (WRF Preprocessing System) Execution Script
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WPS_DIR="$(dirname "$SCRIPT_DIR")"
cd "$WPS_DIR"

echo "=== [1/3] Running GEOGRID for Nested Domains (D01 27km, D02 9km, D03 3km) ==="
if [ ! -f "geogrid.exe" ]; then
    echo "ERROR: geogrid.exe binary not found in $WPS_DIR"
    exit 1
fi
./geogrid.exe > geogrid.log 2>&1
echo "GEOGRID completed successfully. Output files: geo_em.d01.nc, geo_em.d02.nc, geo_em.d03.nc"

echo "=== [2/3] Running UNGRIB for ERA5 Forcing ==="
if [ ! -f "ungrib.exe" ]; then
    echo "ERROR: ungrib.exe binary not found in $WPS_DIR"
    exit 1
fi
./ungrib.exe > ungrib.log 2>&1
echo "UNGRIB completed successfully. Output files: FILE:YYYY-MM-DD_HH"

echo "=== [3/3] Running METGRID to Interpolate Horizontally onto WRF Grids ==="
if [ ! -f "metgrid.exe" ]; then
    echo "ERROR: metgrid.exe binary not found in $WPS_DIR"
    exit 1
fi
./metgrid.exe > metgrid.log 2>&1
echo "METGRID completed successfully. Output files: met_em.d01.*, met_em.d02.*, met_em.d03.*"
echo "=== WPS Preprocessing Workflow Complete ==="
