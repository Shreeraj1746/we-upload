#!/bin/bash

# Script to test pre-push hooks locally
# This will run all pre-push hooks without actually pushing code

set -e  # Exit on error

echo "===== Running pre-push hooks ====="
echo

# Run pre-commit with specific stages
pre-commit run --hook-stage pre-push

echo
echo "===== All pre-push hooks passed! ====="
