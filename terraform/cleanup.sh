#!/bin/bash

# This script cleans up the Terraform infrastructure for the specified environment

# Default environment is dev
ENVIRONMENT=${1:-dev}

# Check if the environment directory exists
if [ ! -d "environments/$ENVIRONMENT" ]; then
  echo "Error: Environment '$ENVIRONMENT' not found!"
  echo "Available environments:"
  ls -1 environments/
  exit 1
fi

# Navigate to the environment directory
cd "environments/$ENVIRONMENT"

# Ask for confirmation
echo "WARNING: This will destroy all resources in the $ENVIRONMENT environment!"
read -p "Are you sure you want to proceed? (type 'yes' to confirm): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Cleanup canceled."
  exit 0
fi

# Destroy the infrastructure
echo "Destroying Terraform infrastructure..."
terraform destroy -auto-approve

echo "Cleanup of $ENVIRONMENT environment completed successfully!"
