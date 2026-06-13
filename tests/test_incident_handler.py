import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch


class FakeClient:
    def publish(self, **_kwargs):
        return {"MessageId": "test-message-id"}

    def invoke_model(self, **_kwargs):
        raise AssertionError("Bedrock should not be called by these unit tests")


def load_incident_handler():
    fake_boto3 = types.SimpleNamespace(client=lambda *_args, **_kwargs: FakeClient())

    with patch.dict(sys.modules, {"boto3": fake_boto3}), patch.dict(
        os.environ,
        {
            "NOTIFICATION_TOPIC_ARN": "arn:aws:sns:us-east-1:123456789012:test",
            "AWS_REGION_NAME": "us-east-1",
        },
    ):
        return importlib.reload(importlib.import_module("lambda.incident_handler"))


class IncidentHandlerTests(unittest.TestCase):
    def test_extract_current_value_from_state_reason(self):
        handler = load_incident_handler()

        value = handler.extract_current_value(
            "Threshold Crossed: 2 datapoints [91.5, 88.2] were greater than threshold."
        )

        self.assertEqual(value, "91.5")

    def test_extract_alarm_data_reads_instance_dimension(self):
        handler = load_incident_handler()
        payload = {
            "AlarmName": "high-cpu",
            "NewStateValue": "ALARM",
            "OldStateValue": "OK",
            "NewStateReason": "Threshold Crossed: [91.5]",
            "StateChangeTime": "2026-06-07T00:00:00Z",
            "Trigger": {
                "MetricName": "CPUUtilization",
                "Namespace": "AWS/EC2",
                "Threshold": 70,
                "ComparisonOperator": "GreaterThanThreshold",
                "Dimensions": [{"name": "InstanceId", "value": "i-1234567890"}],
            },
        }
        record = {"Sns": {"TopicArn": "arn:aws:sns:us-east-1:123456789012:test"}}

        alarm = handler.extract_alarm_data(payload, record)

        self.assertEqual(alarm["instance_id"], "i-1234567890")
        self.assertEqual(alarm["metric_name"], "CPUUtilization")
        self.assertEqual(alarm["current_value"], "91.5")
        self.assertEqual(alarm["severity"], "HIGH")

    def test_determine_severity_maps_threshold_breach_to_medium(self):
        handler = load_incident_handler()

        severity = handler.determine_severity({
            "state": "ALARM",
            "metric_name": "CPUUtilization",
            "current_value": "75",
            "threshold": 70,
        })

        self.assertEqual(severity, "MEDIUM")

    def test_determine_severity_maps_recovery_to_low(self):
        handler = load_incident_handler()

        severity = handler.determine_severity({
            "state": "OK",
            "metric_name": "CPUUtilization",
            "current_value": "21",
            "threshold": 70,
        })

        self.assertEqual(severity, "LOW")

    def test_format_notification_includes_calculated_severity(self):
        handler = load_incident_handler()

        message = handler.format_notification({
            "alarm_name": "high-cpu",
            "instance_id": "i-1234567890",
            "metric_name": "CPUUtilization",
            "namespace": "AWS/EC2",
            "state": "ALARM",
            "previous_state": "OK",
            "threshold": 70,
            "current_value": "91.5",
            "severity": "HIGH",
            "region": "us-east-1",
            "timestamp": "2026-06-07T00:00:00Z",
            "reason": "Threshold Crossed: [91.5]",
        }, "SUMMARY: CPU alarm fired.")

        self.assertIn("Calculated Severity: HIGH", message)

    def test_validate_bedrock_response_falls_back_on_generic_text(self):
        handler = load_incident_handler()

        response = handler.validate_bedrock_response(
            "I do not have enough information to determine the cause. " * 5
        )

        self.assertIn("SUMMARY: CloudWatch alarm triggered", response)
        self.assertIn("SEVERITY: UNKNOWN", response)


if __name__ == "__main__":
    unittest.main()
