# Include common configuration from the dev environment
include {
  path = find_in_parent_folders("terragrunt.hcl")
}

# Local variables specific to this module
locals {
  # Load environment-specific variables
  env_vars = read_terragrunt_config(find_in_parent_folders("env.hcl"))

  # Create a name prefix for resources
  name_prefix = "we-upload-${local.env_vars.locals.env}"
}

# Define the Terraform module source
terraform {
  source = "../../../terraform/modules/app"
}

# Define dependencies on other modules
dependency "vpc" {
  config_path = "../vpc"

  # Configure mock outputs for plan and validate commands
  mock_outputs = {
    vpc_id            = "mock-vpc-id"
    public_subnet_ids = ["mock-public-subnet-1", "mock-public-subnet-2"]
    private_subnet_ids = ["mock-private-subnet-1", "mock-private-subnet-2"]
  }
}

dependency "s3" {
  config_path = "../s3"

  # Configure mock outputs for plan and validate commands
  mock_outputs = {
    bucket_id  = "mock-bucket-id"
    bucket_arn = "mock-bucket-arn"
  }
}

# Inputs to pass to the Terraform module
inputs = {
  name                  = local.name_prefix
  vpc_id                = dependency.vpc.outputs.vpc_id
  public_subnet_ids     = dependency.vpc.outputs.public_subnet_ids
  private_subnet_ids    = dependency.vpc.outputs.private_subnet_ids
  instance_type         = local.env_vars.locals.instance_type
  s3_bucket_name        = dependency.s3.outputs.bucket_id
  s3_bucket_arn         = dependency.s3.outputs.bucket_arn
  db_instance_class     = local.env_vars.locals.db_instance_class
  db_allocated_storage  = local.env_vars.locals.db_allocated_storage
  db_name               = local.env_vars.locals.db_name
  db_username           = local.env_vars.locals.db_username
  db_password           = get_env("TF_VAR_db_password", "temp-password-for-planning")
  api_secret_key        = get_env("TF_VAR_api_secret_key", "temp-secret-key-for-planning")
  ecr_repository        = get_env("TF_VAR_ecr_repository")
  image_tag             = get_env("TF_VAR_image_tag", "latest")
  key_name              = get_env("TF_VAR_key_name", null)
}
