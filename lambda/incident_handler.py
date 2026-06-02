import json
import os
import re
import traceback
from datetime import datetime, timezone

import boto3


sns_client = boto3.client("sns")
bedrock_client = boto3.client(
    "bedrock-runtime",
    region_name=os.environ.get("AWS_REGION_NAME", "us-east-1")
)

NOTIFICATION_TOPIC_ARN = os.environ["NOTIFICATION_TOPIC_ARN"]
BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-3-haiku-20240307-v1:0"
)


def lambda_handler(event, context):
    print("Received event:")
    print(json.dumps(event, indent=2))

    try:
        for record in event.get("Records", []):
            sns_message = record.get("Sns", {}).get("Message", "{}")
            alarm_payload = json.loads(sns_message)

            alarm_data = extract_alarm_data(alarm_payload, record)
            ai_summary = generate_bedrock_summary(alarm_data)
            validated_summary = validate_bedrock_response(ai_summary)

            final_message = format_notification(alarm_data, validated_summary)

            sns_client.publish(
                TopicArn=NOTIFICATION_TOPIC_ARN,
                Subject=f"AWS Incident Alert: {alarm_data['alarm_name']}",
                Message=final_message
            )

            print("Notification sent successfully.")

        return {
            "statusCode": 200,
            "body": "Processed CloudWatch alarm event successfully"
        }

    except Exception as error:
        print("Error processing alarm event:")
        print(str(error))
        print(traceback.format_exc())

        fallback_message = get_fallback_message(str(error))

        sns_client.publish(
            TopicArn=NOTIFICATION_TOPIC_ARN,
            Subject="AWS Incident Alert: Lambda Processing Failed",
            Message=fallback_message
        )

        return {
            "statusCode": 500,
            "body": "Failed to process CloudWatch alarm event"
        }


def extract_alarm_data(alarm_payload, record):
    trigger = alarm_payload.get("Trigger", {})
    dimensions = trigger.get("Dimensions", [])

    instance_id = "unknown"
    for dimension in dimensions:
        if dimension.get("name") == "InstanceId":
            instance_id = dimension.get("value", "unknown")

    topic_arn = record.get("Sns", {}).get("TopicArn", "")
    region = topic_arn.split(":")[3] if ":" in topic_arn else os.environ.get("AWS_REGION_NAME", "us-east-1")

    state_reason = alarm_payload.get("NewStateReason", "No state reason provided")
    current_value = extract_current_value(state_reason)

    return {
        "alarm_name": alarm_payload.get("AlarmName", "unknown"),
        "instance_id": instance_id,
        "metric_name": trigger.get("MetricName", "unknown"),
        "namespace": trigger.get("Namespace", "unknown"),
        "threshold": trigger.get("Threshold", "unknown"),
        "comparison_operator": trigger.get("ComparisonOperator", "unknown"),
        "state": alarm_payload.get("NewStateValue", "unknown"),
        "previous_state": alarm_payload.get("OldStateValue", "unknown"),
        "reason": state_reason,
        "current_value": current_value,
        "region": region,
        "timestamp": alarm_payload.get(
            "StateChangeTime",
            datetime.now(timezone.utc).isoformat()
        )
    }


def extract_current_value(state_reason):
    try:
        matches = re.findall(r"\[(.*?)\]", state_reason)
        if not matches:
            return "not provided"

        datapoints = matches[0].split(",")
        if not datapoints:
            return "not provided"

        return datapoints[0].strip()

    except Exception:
        return "not provided"


def generate_bedrock_summary(alarm_data):
    prompt = f"""
You are an AWS Site Reliability Engineer assistant.

A real CloudWatch alarm has fired with the following exact details:

- Alarm Name: {alarm_data['alarm_name']}
- Resource: {alarm_data['instance_id']}
- Metric: {alarm_data['metric_name']}
- Namespace: {alarm_data['namespace']}
- Threshold: {alarm_data['threshold']}
- Comparison Operator: {alarm_data['comparison_operator']}
- Current Value: {alarm_data['current_value']}
- Alarm State: {alarm_data['state']}
- Previous State: {alarm_data['previous_state']}
- Region: {alarm_data['region']}
- Timestamp: {alarm_data['timestamp']}
- CloudWatch Reason: {alarm_data['reason']}

Using ONLY the information above, provide:

1. SUMMARY: 2 sentences max explaining what is happening to this specific resource.
2. LIKELY CAUSE: 1-2 sentences based only on the metric, threshold, and alarm reason.
3. IMMEDIATE ACTIONS: Numbered list, max 5 steps, specific to this metric.
4. SEVERITY: LOW / MEDIUM / HIGH. If current value is not provided, say UNKNOWN.

RULES:
- Do not mention AWS services unrelated to this metric.
- Do not give generic AWS advice.
- Base every recommendation on the actual values provided above.
- If the current value is not provided, do not invent one.
- Respond in plain text only. No markdown.
"""

    response = bedrock_client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def validate_bedrock_response(response_text):
    if not response_text or len(response_text.strip()) < 100:
        return get_fallback_summary("Bedrock response was too short or empty.")

    hallucination_signals = [
        "as an ai",
        "i do not have enough information",
        "i don't have enough information",
        "i cannot determine",
        "please consult aws documentation",
        "consult the documentation",
        "i am unable to"
    ]

    lower_response = response_text.lower()

    for signal in hallucination_signals:
        if signal in lower_response:
            return get_fallback_summary(f"Detected generic response signal: {signal}")

    return response_text


def get_fallback_summary(reason):
    return f"""SUMMARY: CloudWatch alarm triggered and requires manual review.

LIKELY CAUSE: The alert was generated from CloudWatch alarm data, but AI-generated analysis was not used because: {reason}

IMMEDIATE ACTIONS:
1. Open the CloudWatch alarm and review the metric graph.
2. Confirm the affected resource and alarm threshold.
3. Check recent deployments, traffic changes, or process-level resource usage.
4. Review application and system logs for errors.
5. Escalate to the on-call engineer if the alarm remains active.

SEVERITY: UNKNOWN - requires manual assessment"""


def format_notification(alarm_data, summary):
    return f"""AWS INFRASTRUCTURE INCIDENT ALERT

Alarm Name: {alarm_data['alarm_name']}
Resource: {alarm_data['instance_id']}
Metric: {alarm_data['metric_name']}
Namespace: {alarm_data['namespace']}
State: {alarm_data['state']}
Previous State: {alarm_data['previous_state']}
Threshold: {alarm_data['threshold']}
Current Value: {alarm_data['current_value']}
Region: {alarm_data['region']}
Timestamp: {alarm_data['timestamp']}

AI-GENERATED INCIDENT SUMMARY

{summary}

RAW CLOUDWATCH REASON

{alarm_data['reason']}
"""


def get_fallback_message(error_message):
    return f"""AWS INCIDENT HANDLER FAILURE

The Lambda function failed while processing a CloudWatch alarm event.

Error:
{error_message}

Manual fallback actions:
1. Open CloudWatch Alarms in the AWS Console.
2. Review the alarm that recently changed state.
3. Check the monitored EC2 instance metrics.
4. Review Lambda CloudWatch Logs for the full error trace.
5. Confirm Bedrock model access and SNS permissions.

Severity: UNKNOWN - manual review required.
"""
