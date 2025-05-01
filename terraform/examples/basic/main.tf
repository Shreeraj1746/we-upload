module "example" {
  source = "../../modules/s3"

  project_name = "we-upload"
  environment  = "dev"

  enable_lifecycle_rules = true
  expiration_days        = 90
}
