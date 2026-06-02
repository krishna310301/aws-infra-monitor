output "monitored_instance_id" {
  description = "ID of the monitored EC2 instance"
  value       = aws_instance.monitored_ec2.id
}

output "monitored_instance_public_ip" {
  description = "Public IP address of the monitored EC2 instance"
  value       = aws_instance.monitored_ec2.public_ip
}

output "cloudwatch_alarm_name" {
  description = "Name of the CloudWatch high CPU alarm"
  value       = aws_cloudwatch_metric_alarm.high_cpu_alarm.alarm_name
}

output "alarm_trigger_topic_arn" {
  description = "SNS topic ARN used by CloudWatch to trigger Lambda"
  value       = aws_sns_topic.alarm_trigger_topic.arn
}

output "notification_topic_arn" {
  description = "SNS topic ARN used for email notifications"
  value       = aws_sns_topic.notification_topic.arn
}

output "lambda_function_name" {
  description = "Name of the incident handler Lambda function"
  value       = aws_lambda_function.incident_handler.function_name
}

