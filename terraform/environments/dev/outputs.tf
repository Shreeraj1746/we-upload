output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "List of IDs of the public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of IDs of the private subnets"
  value       = module.vpc.private_subnet_ids
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.s3.s3_bucket_name
}

output "s3_bucket_arn" {
  description = "The ARN of the S3 bucket"
  value       = module.s3.s3_bucket_arn
}

output "ec2_instance_profile_name" {
  description = "The name of the EC2 instance profile"
  value       = module.iam.ec2_instance_profile_name
}

output "ec2_role_name" {
  description = "The name of the EC2 IAM role"
  value       = module.iam.ec2_role_name
}

output "ec2_instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = module.ec2.ec2_instance_public_ip
}

output "ec2_instance_id" {
  description = "ID of the EC2 instance"
  value       = module.ec2.ec2_instance_id
}

output "ec2_security_group_id" {
  description = "ID of the EC2 security group"
  value       = module.ec2.ec2_security_group_id
}

output "rds_endpoint" {
  description = "Endpoint of the RDS instance"
  value       = module.rds.rds_instance_endpoint
}

output "rds_db_name" {
  description = "Name of the database"
  value       = var.db_name
}
