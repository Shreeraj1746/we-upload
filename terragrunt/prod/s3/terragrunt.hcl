# Include common configuration from the prod environment
include {
  path = find_in_parent_folders("terragrunt.hcl")
}

# Local variables specific to this module
locals {
  # Load environment-specific variables
  env_vars = read_terragrunt_config(find_in_parent_folders("env.hcl"))

  # Create a unique bucket name using a random suffix
  env = local.env_vars.locals.env
}

# Define the Terraform module source
terraform {
  source = "../../../terraform/modules/s3"
}

# Inputs to pass to the Terraform module
inputs = {
  bucket_name = "we-upload-files-${local.env}-${get_env("TF_VAR_random_suffix", uuid())}"
  cors_allowed_origins = local.env_vars.locals.cors_allowed_origins
}
