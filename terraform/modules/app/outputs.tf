output "api_security_group_id" {
  description = "ID of the API security group"
  value       = aws_security_group.api.id
}

output "db_security_group_id" {
  description = "ID of the database security group"
  value       = aws_security_group.db.id
}

output "ec2_instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.api.id
}

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.api.public_ip
}

output "db_endpoint" {
  description = "Endpoint of the RDS database"
  value       = aws_db_instance.postgres.endpoint
}

output "db_name" {
  description = "Name of the database"
  value       = aws_db_instance.postgres.db_name
}

output "iam_role_name" {
  description = "Name of the IAM role for EC2"
  value       = aws_iam_role.ec2_role.name
}

output "iam_role_arn" {
  description = "ARN of the IAM role for EC2"
  value       = aws_iam_role.ec2_role.arn
}
