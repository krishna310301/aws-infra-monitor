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

```

## Tech Stack

- AWS EC2
- Amazon CloudWatch
- Amazon SNS
- AWS Lambda
- Amazon Bedrock
- Terraform
- Python
- GitHub Actions

## Key Features

- Provisioned AWS infrastructure using Terraform
- Monitored EC2 CPU utilization with CloudWatch alarms
- Used separate SNS topics for alarm triggering and email notification
- Built a Lambda function to parse CloudWatch alarm payloads
- Integrated Amazon Bedrock using a Claude Haiku inference profile
- Generated AI incident summaries, likely causes, recommended actions, and severity
- Added fallback handling when AI generation fails
- Added GitHub Actions workflow for Terraform validation

## Bedrock Model / Inference Profile

The Lambda function uses the following Bedrock inference profile through the `BEDROCK_MODEL_ID` environment variable:

```text
us.anthropic.claude-haiku-4-5-20251001-v1:0
```

## Validation Evidence

The project was validated with:

- Terraform state/output showing provisioned resources
- SNS email subscription confirmation
- Manual SNS test publish with MessageId
- AI-generated incident email notification
- CloudWatch Logs confirming successful Lambda execution
- GitHub Actions Terraform validation workflow

## Example Incident Output

```text
SUMMARY:
EC2 instance i-xxxxxxxxxxxxxxxxx is experiencing sustained high CPU utilization, exceeding the configured alarm threshold.

LIKELY CAUSE:
Recent datapoints indicate sustained CPU load rather than a transient spike. This may be caused by increased application workload, a runaway process, or inadequate instance sizing.

IMMEDIATE ACTIONS:
1. Connect to the instance and inspect CPU-consuming processes.
2. Determine whether the workload is expected or unexpected.
3. Restart or stop the offending process if required.
4. Evaluate instance sizing if the load is expected.
5. Continue monitoring CloudWatch metrics.

SEVERITY:
HIGH
```

## CI/CD

This repository includes a GitHub Actions workflow that runs:

```bash
terraform fmt -check
terraform init -backend=false
terraform validate
```

## Security Notes

- Terraform state files and local variable files are excluded from version control.
- The Lambda IAM role uses scoped permissions for CloudWatch Logs and SNS publishing.
- - Bedrock invocation is scoped to the configured inference profile and foundation model. AWS Marketplace read/subscribe permissions are included because Anthropic Bedrock models may require Marketplace-backed access activation in some AWS accounts.
- Screenshots and local validation evidence are not committed to avoid exposing account-specific details.

## Future Improvements

- Add Systems Manager Session Manager support for secure EC2 access
- Add automated CPU stress test script
- Add Slack or Microsoft Teams notification integration
- Store incident history in DynamoDB
- Add EventBridge routing for multi-alarm workflows
- Tighten Bedrock IAM permission to a specific inference profile ARN
