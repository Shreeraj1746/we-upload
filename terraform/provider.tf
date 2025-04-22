provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "we-upload"
      Environment = "dev"
      Terraform   = "true"
    }
  }
}
