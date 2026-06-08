variable "aws_region" {
  description = "AWS region for all project resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for naming AWS resources"
  type        = string
  default     = "aws-infra-monitor"
}

variable "notification_email" {
  description = "Email address that receives SNS incident notifications"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type used for the monitored instance"
  type        = string
  default     = "t3.micro"
}

variable "cpu_alarm_threshold" {
  description = "CPU utilization percentage threshold for the CloudWatch alarm"
  type        = number
  default     = 70
}

variable "enable_startup_cpu_stress" {
  description = "Run a temporary CPU load loop on instance boot to trigger the CloudWatch alarm for demo validation"
  type        = bool
  default     = false
}

variable "startup_cpu_stress_seconds" {
  description = "Duration in seconds for optional startup CPU load"
  type        = number
  default     = 300
}

variable "bedrock_model_id" {
  description = "Amazon Bedrock model ID used for incident summary generation"
  type        = string
  default     = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
}
