#!/usr/bin/env bash
# ==============================================================================
# SAMEER — Official WRF Geographic Static Dataset Downloader
# ==============================================================================
# WRF requires high-resolution static terrain, soil categories, and land-use data (USGS/MODIS).
# This script downloads official datasets from the UCAR/NCAR repository.
set -e

TARGET_DIR="${1:-/data/static/WPS_GEOG}"
echo "Downloading WRF Static Geographic Data to: $TARGET_DIR"
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

BASE_URL="https://www2.mmm.ucar.edu/wrf/src/wps_files"
GEOG_ARCHIVE="geog_high_res_mandatory.tar.gz"

if [ ! -f "$GEOG_ARCHIVE" ]; then
    echo "Fetching $GEOG_ARCHIVE from UCAR..."
    wget -c "${BASE_URL}/${GEOG_ARCHIVE}"
    echo "Extracting geographic dataset..."
    tar -xzf "$GEOG_ARCHIVE"
else
    echo "Geographic dataset archive already exists in $TARGET_DIR"
fi

echo "Geographic dataset ready. Update 'geog_data_path' in namelist.wps to: $TARGET_DIR"
