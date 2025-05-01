#!/bin/bash
set -e

# Check if terraform-docs is installed
if ! command -v terraform-docs &> /dev/null; then
  echo "Error: terraform-docs is not installed. Please install it first:"
  echo "  - macOS: brew install terraform-docs"
  echo "  - Linux: See https://terraform-docs.io/user-guide/installation/"
  exit 1
fi

# Check terraform-docs version
TERRAFORM_DOCS_VERSION=$(terraform-docs --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
MIN_VERSION="0.16.0"

if [[ "$(printf '%s\n' "$MIN_VERSION" "$TERRAFORM_DOCS_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]]; then
  echo "Error: terraform-docs version $TERRAFORM_DOCS_VERSION is too old. Please upgrade to version $MIN_VERSION or newer."
  exit 1
fi

# Get repository root directory
REPO_ROOT="$(git rev-parse --show-toplevel)"

# Generate documentation for the main terraform directory
echo "Generating documentation for terraform root directory"
cd "$REPO_ROOT/terraform"
terraform-docs markdown table --output-file README.md .
if [ -f "README.md" ]; then
  echo "✅ README.md successfully generated in terraform"
else
  echo "❌ Failed to create README.md in terraform"
fi

# Generate documentation for each module directory
MODULE_DIRS=$(find "$REPO_ROOT/terraform/modules" -mindepth 1 -maxdepth 1 -type d)
for dir in $MODULE_DIRS; do
  echo "Generating documentation for $dir"
  cd "$dir"
  terraform-docs markdown table --output-file README.md .
  if [ -f "README.md" ]; then
    echo "✅ README.md successfully generated in $dir"
  else
    echo "❌ Failed to create README.md in $dir"
  fi
done

echo "Terraform documentation generation completed successfully."
echo "Generated documentation for the following modules:"
find "$REPO_ROOT/terraform/modules" -name "README.md" | sort
