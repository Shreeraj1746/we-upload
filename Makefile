.PHONY: init init-terragrunt plan-dev apply-dev plan-prod apply-prod plan-all apply-all clean terraform-docs

# Common variables
TF_STATE_BUCKET ?= we-upload-terraform-state
TF_LOCK_TABLE ?= we-upload-terraform-locks
AWS_REGION ?= ap-south-1

# Init scripts
init: init-terragrunt

init-terragrunt:
	@echo "Initializing Terragrunt infrastructure..."
	@TF_STATE_BUCKET=$(TF_STATE_BUCKET) TF_LOCK_TABLE=$(TF_LOCK_TABLE) AWS_REGION=$(AWS_REGION) ./scripts/init-terragrunt.sh

# Development environment
plan-dev:
	@echo "Planning development environment..."
	@cd terragrunt/dev && terragrunt run-all plan

apply-dev:
	@echo "Applying development environment..."
	@cd terragrunt/dev && terragrunt run-all apply

# Production environment
plan-prod:
	@echo "Planning production environment..."
	@cd terragrunt/prod && terragrunt run-all plan

apply-prod:
	@echo "Applying production environment..."
	@cd terragrunt/prod && terragrunt run-all apply

# All environments
plan-all:
	@echo "Planning all environments..."
	@cd terragrunt && terragrunt run-all plan

apply-all:
	@echo "Applying all environments..."
	@cd terragrunt && terragrunt run-all apply

# Generate Terraform documentation
terraform-docs:
	@echo "Generating Terraform documentation..."
	@./scripts/generate_terraform_docs.sh

# Clean the Terraform cache
clean:
	@echo "Cleaning Terragrunt cache..."
	@find . -name ".terragrunt-cache" -type d -exec rm -rf {} +

# Help
help:
	@echo "Available targets:"
	@echo "  init            - Initialize Terragrunt infrastructure"
	@echo "  plan-dev        - Plan changes for development environment"
	@echo "  apply-dev       - Apply changes to development environment"
	@echo "  plan-prod       - Plan changes for production environment"
	@echo "  apply-prod      - Apply changes to production environment"
	@echo "  plan-all        - Plan changes for all environments"
	@echo "  apply-all       - Apply changes to all environments"
	@echo "  terraform-docs  - Generate Terraform documentation"
	@echo "  clean           - Clean Terragrunt cache"
	@echo "  help            - Show this help message"
	@echo ""
	@echo "Environment variables:"
	@echo "  TF_STATE_BUCKET - S3 bucket for Terraform state (default: we-upload-terraform-state)"
	@echo "  TF_LOCK_TABLE   - DynamoDB table for Terraform locks (default: we-upload-terraform-locks)"
	@echo "  AWS_REGION      - AWS region (default: ap-south-1)"

# Default target
.DEFAULT_GOAL := help
