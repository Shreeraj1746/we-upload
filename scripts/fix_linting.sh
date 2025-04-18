#!/bin/bash
# Script to help automate fixing common linting issues

set -e

echo "Running ruff with automated fixes..."
ruff check --fix .

echo "Running ruff-format..."
ruff format .

echo "Running pre-commit hooks to check for remaining issues..."
pre-commit run

echo "Done! Note that some issues may still need manual fixes."
