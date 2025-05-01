#!/bin/bash

# Script to run integration tests for pre-commit hook
# This ensures proper environment setup and cleanup when running from pre-commit

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

# Determine which docker compose command to use
# First try the modern "docker compose" format
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    # Fall back to legacy "docker-compose" format
    COMPOSE_CMD="docker-compose"
fi

# Ensure clean environment
echo "Stopping any existing Docker Compose services..."
$COMPOSE_CMD down -v >/dev/null 2>&1 || true

# Start the containers
echo "Starting Docker Compose services for integration tests..."
$COMPOSE_CMD up -d

# Wait for services to be ready (the tests have their own wait mechanism)
echo "Waiting for services to be ready..."
sleep 5

# Run the integration tests
echo "Running integration tests..."
python -m pytest tests/test_basic_file_api.py tests/test_api_integration.py -v

# Get the test result
TEST_RESULT=$?

# Clean up regardless of test result
echo "Cleaning up Docker Compose environment..."
$COMPOSE_CMD down -v

# Exit with the test result
exit $TEST_RESULT
