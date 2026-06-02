# AWS AI-Powered Infrastructure Monitor

An AWS infrastructure monitoring project that detects EC2 CPU threshold breaches, processes CloudWatch alarm context with AWS Lambda, generates an AI incident summary using Amazon Bedrock, and sends email notifications through Amazon SNS.

## Architecture

```text
EC2 Instance
     |
     | CPUUtilization metric
     v
CloudWatch Alarm
     |
     | Alarm state change
     v
SNS Topic: alarm-trigger-topic
     |
     | Lambda subscription
     v
Lambda Function: incident_handler.py
     |
     | Parses alarm context
     | Invokes Amazon Bedrock
     | Generates incident summary
     v
SNS Topic: notification-topic
     |
     v
Email notification
