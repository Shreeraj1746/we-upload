#!/bin/bash

# Script to run unit tests for pre-commit hook
# This ensures proper environment setup when running from pre-commit

set -e  # Exit on error

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    . venv/bin/activate
    pip install -e ".[dev]"
else
    . venv/bin/activate
fi

# Run the unit tests
echo "Running unit tests..."
python -m pytest tests/ --ignore=tests/test_e2e_upload_download.py --ignore=tests/test_basic_file_api.py
