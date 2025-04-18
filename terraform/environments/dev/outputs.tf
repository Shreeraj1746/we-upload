output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "s3_bucket_name" {
  description = "The name of the S3 bucket"
  value       = module.s3.bucket_id
}

output "api_endpoint" {
  description = "The public DNS of the API server"
  value       = "http://${aws_instance.api.public_dns}:8000"
}

output "db_endpoint" {
  description = "The endpoint of the RDS database"
  value       = aws_db_instance.postgres.address
  sensitive   = true
}

output "api_instance_id" {
  description = "The ID of the API EC2 instance"
  value       = aws_instance.api.id
}
