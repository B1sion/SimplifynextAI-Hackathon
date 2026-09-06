"""Make one inexpensive local Bedrock request using the standard AWS chain."""

import json
import os
from typing import Any

import boto3


REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")


def main() -> None:
    client = boto3.client("bedrock-runtime", region_name=REGION)
    if MODEL_ID.startswith("amazon.nova-"):
        request = {
            "messages": [{"role": "user", "content": [{"text": "Reply with exactly: Bedrock works"}]}],
            "inferenceConfig": {"maxTokens": 16, "temperature": 0},
        }
    else:
        request = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [{"role": "user", "content": "Reply with exactly: Bedrock works"}],
            "max_tokens": 16,
            "temperature": 0,
        }
    body = json.dumps(request)
    try:
        response = client.invoke_model(
            modelId=MODEL_ID,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        envelope: dict[str, Any] = json.loads(response["body"].read())
        if MODEL_ID.startswith("amazon.nova-"):
            text = envelope.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "").strip()
            stop_reason = envelope.get("stopReason")
        else:
            text = envelope.get("content", [{}])[0].get("text", "").strip()
            stop_reason = envelope.get("stop_reason")
        print(json.dumps({"region": REGION, "model_id": MODEL_ID, "text": text, "stop_reason": stop_reason}))
    except Exception as error:
        print(json.dumps({"region": REGION, "model_id": MODEL_ID, "api_operation": "InvokeModel", "error_type": type(error).__name__, "error": str(error)}))
        raise


if __name__ == "__main__":
    main()