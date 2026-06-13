# Incident Triage Runbook

This runbook covers the first-response path for the AWS Incident Triage Pipeline when a CloudWatch alarm creates an incident notification.

## Initial Triage

1. Open the incident email and confirm:
   - alarm name
   - affected instance ID
   - metric name
   - current value
   - threshold
   - calculated severity
   - previous and current alarm state
2. Open the CloudWatch alarm in the AWS console and review the metric graph around the state-change timestamp.
3. Check whether the alert is a new `OK -> ALARM` event, a recovery `ALARM -> OK` event, or an `INSUFFICIENT_DATA` transition.
4. Review recent changes that could explain the signal: deploys, traffic changes, scheduled jobs, test load, or instance startup activity.

## Severity Handling

The Lambda calculates severity before calling Bedrock so the notification still has useful triage context if model output is unavailable.

| Condition | Severity |
| --- | --- |
| Alarm state is `OK` | `LOW` |
| Alarm state is `INSUFFICIENT_DATA` | `UNKNOWN` |
| Alarm state is `ALARM` and value is missing | `UNKNOWN` |
| CPU utilization is 90% or higher | `HIGH` |
| Current value is 1.5x threshold or higher | `HIGH` |
| Current value is at or above threshold | `MEDIUM` |

## Common Response Paths

### High CPU Alarm

1. Confirm the CPU graph shows sustained usage across the alarm evaluation periods.
2. Check whether the optional startup CPU stress setting was enabled for validation.
3. Inspect system/application logs for process-level CPU spikes.
4. Check recent deployments or scheduled jobs.
5. If the alarm remains active, escalate to the service owner or on-call engineer with the instance ID and alarm timeline.

### Bedrock Summary Missing or Generic

1. Use the deterministic fallback summary in the email.
2. Check Lambda logs for Bedrock invocation errors.
3. Confirm the configured model ID is available in the selected AWS region.
4. Confirm the account has Bedrock model access enabled.
5. Re-run the safe SNS test payload after fixing model access or permissions.

### No Email Received

1. Confirm the SNS email subscription is accepted.
2. Check the notification topic for recent publish attempts.
3. Review the Lambda log group for handler errors.
4. Confirm the Lambda role can publish to the notification SNS topic.
5. Confirm the alarm trigger topic has the Lambda subscription attached.

## Validation Commands

Run unit tests:

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
```

Validate Terraform:

```bash
terraform fmt -check
terraform init -backend=false
terraform validate
```

Tail Lambda logs after a test event:

```bash
aws logs tail /aws/lambda/aws-incident-triage-pipeline-incident-handler \
  --region us-east-1 \
  --since 10m
```

## Cleanup

Destroy the environment after validation to avoid EC2 and Bedrock charges:

```bash
terraform destroy
```
