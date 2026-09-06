import json
import os
from typing import Any


class BedrockClientError(RuntimeError):
    """Bedrock was unavailable or returned a non-JSON model response."""


class BedrockNovaClient:
    def __init__(self, client: Any | None = None, region: str | None = None, model_id: str | None = None):
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.model_id = model_id or os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            import boto3
            from botocore.config import Config

            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
                config=Config(connect_timeout=10, read_timeout=120, retries={"max_attempts": 2, "mode": "standard"}),
            )
        return self._client

    def generate_json(self, system_prompt: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = {
            "messages": [{"role": "user", "content": [{"text": f"{system_prompt}\n\nINPUT JSON:\n{json.dumps(payload, ensure_ascii=True)}"}]}],
            "inferenceConfig": {"maxTokens": 4096, "temperature": 0},
        }
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request),
                contentType="application/json",
                accept="application/json",
            )
            envelope = json.loads(response["body"].read())
            text = envelope["output"]["message"]["content"][0]["text"]
            result = self._parse_json(text)
            if not isinstance(result, dict):
                raise BedrockClientError("Bedrock model output was not a JSON object")
            return result
        except BedrockClientError:
            raise
        except Exception as error:
            raise BedrockClientError(f"Bedrock {self.model_id} request failed: {error}") from error

    @staticmethod
    def _parse_json(text: str) -> Any:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            if start < 0:
                raise BedrockClientError("Bedrock model output contained no JSON object")
            try:
                return json.JSONDecoder().raw_decode(cleaned[start:])[0]
            except json.JSONDecodeError as error:
                raise BedrockClientError(f"Bedrock model output contained malformed JSON: {error}") from error

    def evaluate_resume(self, resume: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
        return self.generate_json(
            """Act as an ATS resume evaluator. Compare the resume to the complete job description and return ONLY valid JSON with keys: ats_score (0-100 number), summary (string), strengths (array of strings), weaknesses (array of strings), matched_skills (array of strings), missing_skills (array of strings), keyword_gaps (array of strings), experience_gaps (array of strings), ats_issues (array of strings), high_priority_improvements (array of strings). Use only evidence present in the resume; do not invent candidate facts.""",
            {"resume": resume, "job": job},
        )

    def plan_resume(self, resume: dict[str, Any], job: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
        return self.generate_json(
            """Act as a resume rewrite planner. Return ONLY valid JSON with keys changes, user_recommendations, prohibited_claims. Each change must contain target, action, priority, reason, instruction. Plan truthful edits only; do not rewrite the resume.""",
            {"resume": resume, "job": job, "ats_report": evaluation},
        )

    def rewrite_resume(self, resume: dict[str, Any], job: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        return self.generate_json(
            """Act as a truthful resume writer. Return ONLY a complete ResumeIR JSON object. Apply the rewrite plan for ATS clarity, but preserve every fact, date, title, skill, employer, project, credential, and education claim unless it is already supported by the input resume. Never invent metrics or experience.""",
            {"resume": resume, "job": job, "rewrite_plan": plan},
        )

    def validate_resume(self, authoritative_resume: dict[str, Any], candidate_resume: dict[str, Any]) -> dict[str, Any]:
        return self.generate_json(
            """Act as a resume truthfulness validator. Return ONLY valid JSON with keys valid (boolean), unsupported_additions (array of objects with category, claim, reason), changed_dates (array of strings), inflated_titles (array of strings), and summary (string). Reject unsupported facts, invented metrics, skills, technologies, responsibilities, credentials, projects, education, dates, titles, or seniority.""",
            {"authoritative_resume": authoritative_resume, "candidate_resume": candidate_resume},
        )