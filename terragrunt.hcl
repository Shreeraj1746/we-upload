# Root terragrunt.hcl - contains common configuration for all environments

remote_state {
  backend = "s3"
  config = {
    bucket         = "${get_env("TF_STATE_BUCKET", "we-upload-terraform-state")}"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "ap-south-1"
    encrypt        = true
    dynamodb_table = "we-upload-terraform-locks"
  }
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
}

# Generate providers.tf file for each module
generate "providers" {
  path      = "providers.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "aws" {
  region = "${local.aws_region}"
}
EOF
}

# Include common variables for all environments
locals {
  # Parse environment-specific variables from terragrunt.hcl
  environment_vars = read_terragrunt_config(find_in_parent_folders("env.hcl"))

  # Default settings
  aws_region = local.environment_vars.locals.aws_region

  # Common tags for all resources
  common_tags = {
    Project     = "we-upload"
    Environment = local.environment_vars.locals.env
    ManagedBy   = "Terragrunt"
  }
}

# Inputs to pass down to all Terraform modules
inputs = {
  aws_region = local.aws_region
  tags       = local.common_tags
}
