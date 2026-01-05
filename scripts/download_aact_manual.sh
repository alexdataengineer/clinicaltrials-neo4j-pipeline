#!/bin/bash
# Manual AACT download helper script
# Use this if automatic download fails

set -e

DATA_DIR="${AACT_DATA_DIR:-data/raw}"
ZIP_FILE="${DATA_DIR}/aact_pipe_delimited.zip"

echo "AACT Manual Download Helper"
echo "============================"
echo ""
echo "This script helps you download AACT data manually."
echo ""
echo "Option 1: Direct download (if URL is known)"
echo "  Visit: https://aact.ctti-clinicaltrials.org/downloads"
echo "  Download the 'Pipe-Delimited Files' zip"
echo "  Place it at: ${ZIP_FILE}"
echo ""
echo "Option 2: Use this script to download (if URL works)"
echo ""

# Try to download from common AACT URL
DOWNLOAD_URL="https://aact.ctti-clinicaltrials.org/static/exported_files/monthly/pipe_delimited_files.zip"

if [ -f "$ZIP_FILE" ]; then
    echo "File already exists: $ZIP_FILE"
    echo "Delete it first if you want to re-download."
    exit 0
fi

echo "Attempting to download from: $DOWNLOAD_URL"
echo ""

mkdir -p "$DATA_DIR"

if command -v curl &> /dev/null; then
    curl -L -o "$ZIP_FILE" "$DOWNLOAD_URL"
elif command -v wget &> /dev/null; then
    wget -O "$ZIP_FILE" "$DOWNLOAD_URL"
else
    echo "Error: Neither curl nor wget found. Please download manually:"
    echo "  1. Visit https://aact.ctti-clinicaltrials.org/downloads"
    echo "  2. Download 'Pipe-Delimited Files'"
    echo "  3. Place at: $ZIP_FILE"
    exit 1
fi

if [ -f "$ZIP_FILE" ]; then
    echo ""
    echo "✓ Download complete: $ZIP_FILE"
    echo "You can now run the pipeline."
else
    echo ""
    echo "✗ Download failed. Please download manually:"
    echo "  1. Visit https://aact.ctti-clinicaltrials.org/downloads"
    echo "  2. Download 'Pipe-Delimited Files'"
    echo "  3. Place at: $ZIP_FILE"
    exit 1
fi

