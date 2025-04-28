output "log_group_name" {
  description = "Name of the CloudWatch Log Group"
  value       = aws_cloudwatch_log_group.api_logs.name
}

output "log_group_arn" {
  description = "ARN of the CloudWatch Log Group"
  value       = aws_cloudwatch_log_group.api_logs.arn
}

output "cpu_alarm_arn" {
  description = "ARN of the CPU High Alarm"
  value       = aws_cloudwatch_metric_alarm.cpu_high.arn
}

output "memory_alarm_arn" {
  description = "ARN of the Memory High Alarm"
  value       = aws_cloudwatch_metric_alarm.memory_high.arn
}

output "disk_alarm_arn" {
  description = "ARN of the Disk High Alarm"
  value       = aws_cloudwatch_metric_alarm.disk_high.arn
}
