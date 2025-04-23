#!/bin/bash

# This script deploys the Terraform infrastructure for the specified environment

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

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Plan the changes
echo "Planning Terraform changes..."
terraform plan -out=tfplan

# Ask for confirmation
read -p "Do you want to apply these changes? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
  echo "Deployment canceled."
  exit 0
fi

# Apply the changes
echo "Applying Terraform changes..."
terraform apply tfplan

# Display outputs
echo "Deployment complete! Here are the outputs:"
terraform output

# Cleanup
rm -f tfplan

echo "Deployment to $ENVIRONMENT environment completed successfully!"
echo "To test the infrastructure, follow the testing instructions in the README.md"
