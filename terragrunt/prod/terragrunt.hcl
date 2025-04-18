# Include root terragrunt.hcl
include {
  path = find_in_parent_folders()
}

# Environment-specific variables that are used by all modules
locals {
  # Load environment-specific variables
  env_vars = read_terragrunt_config(find_in_parent_folders("env.hcl"))

  # Extract variables for easier reference
  env                      = local.env_vars.locals.env
  aws_region               = local.env_vars.locals.aws_region
  vpc_cidr_block           = local.env_vars.locals.vpc_cidr_block
  public_subnet_cidr_blocks = local.env_vars.locals.public_subnet_cidr_blocks
  private_subnet_cidr_blocks = local.env_vars.locals.private_subnet_cidr_blocks
  enable_nat_gateway       = local.env_vars.locals.enable_nat_gateway
  instance_type            = local.env_vars.locals.instance_type
  db_instance_class        = local.env_vars.locals.db_instance_class
  db_allocated_storage     = local.env_vars.locals.db_allocated_storage
  db_name                  = local.env_vars.locals.db_name
  db_username              = local.env_vars.locals.db_username
  cors_allowed_origins     = local.env_vars.locals.cors_allowed_origins
}

# Common inputs for all modules in this environment
inputs = {
  environment = local.env
}
