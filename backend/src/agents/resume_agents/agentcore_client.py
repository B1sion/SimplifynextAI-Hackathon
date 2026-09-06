import json
import os
import base64
from collections.abc import Callable
from typing import Any
from uuid import uuid4


class AgentCoreError(RuntimeError):
    """The remote AgentCore boundary failed or returned invalid data."""


class AgentCoreClient:
    def __init__(self, invoke: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None):
        self._invoke = invoke

    def _call(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self._invoke is not None:
            result = self._invoke(operation, payload)
            if not isinstance(result, dict):
                raise AgentCoreError(f"AgentCore returned non-object for {operation}")
            return result
        runtime_arn = os.environ.get("AGENTCORE_RUNTIME_ARN")
        if not runtime_arn:
            raise AgentCoreError("AGENTCORE_RUNTIME_ARN is not configured")
        try:
            import boto3

            client = boto3.client("bedrock-agentcore", region_name=os.getenv("AWS_REGION", "us-east-1"))
            response = client.invoke_agent_runtime(
                agentRuntimeArn=runtime_arn,
                runtimeSessionId=uuid4().hex,
                payload=json.dumps({"operation": operation, "input": payload}).encode("utf-8"),
            )
            body = response.get("response", response.get("output"))
            if hasattr(body, "read"):
                body = body.read()
            if isinstance(body, bytes):
                body = body.decode("utf-8")
            result = json.loads(body) if isinstance(body, str) else body
            if not isinstance(result, dict):
                raise AgentCoreError(f"AgentCore returned non-object for {operation}")
            return result
        except AgentCoreError:
            raise
        except Exception as error:
            raise AgentCoreError(f"AgentCore {operation} failed: {error}") from error

    def parse_job(self, job: dict[str, Any]) -> dict[str, Any]:
        return self._call("parse_job", {"job": job})

    def parse_resume(self, text: str) -> dict[str, Any]:
        return self._call("parse_resume", {"text": text})

    def parse_resume_pdf(self, pdf_bytes: bytes, filename: str = "resume.pdf") -> dict[str, Any]:
        return self._call(
            "parse_resume",
            {
                "document": {
                    "media_type": "application/pdf",
                    "filename": filename,
                    "data_base64": base64.b64encode(pdf_bytes).decode("ascii"),
                }
            },
        )

    def evaluate_resume(self, resume: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
        return self._call("evaluate_resume", {"resume": resume, "job": job})

    def plan_resume(self, resume: dict[str, Any], job: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
        return self._call("plan_resume", {"resume": resume, "job": job, "evaluation": evaluation})

    def rewrite_resume(self, resume: dict[str, Any], job: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        return self._call("rewrite_resume", {"resume": resume, "job": job, "plan": plan})

    def validate_resume(self, authoritative_resume: dict[str, Any], candidate_resume: dict[str, Any]) -> dict[str, Any]:
        return self._call("validate_resume", {"authoritative_resume": authoritative_resume, "candidate_resume": candidate_resume})