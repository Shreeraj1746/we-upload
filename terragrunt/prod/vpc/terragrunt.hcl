# Include common configuration from the prod environment
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
  source = "../../../terraform/modules/vpc"
}

# Inputs to pass to the Terraform module
inputs = {
  name                      = local.name_prefix
  vpc_cidr_block            = local.env_vars.locals.vpc_cidr_block
  public_subnet_cidr_blocks = local.env_vars.locals.public_subnet_cidr_blocks
  private_subnet_cidr_blocks = local.env_vars.locals.private_subnet_cidr_blocks
  availability_zones        = ["${local.env_vars.locals.aws_region}a", "${local.env_vars.locals.aws_region}b"]
  enable_nat_gateway        = local.env_vars.locals.enable_nat_gateway
}
