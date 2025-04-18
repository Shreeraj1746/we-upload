#!/bin/bash
# Script to fix linting issues, commit and push to GitHub

set -e

# Run the linting fix script first
echo "Running linting fixes..."
./scripts/fix_linting.sh || true

# Add changes
echo "Adding changes to git..."
git add .

# Commit changes
echo "Committing changes..."
git commit -m "fix: linting and type checking issues" || true

# Push to GitHub
echo "Pushing to GitHub..."
git push

echo "Done! Changes have been pushed to GitHub."
