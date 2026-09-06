import json
import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class ModelClientError(RuntimeError):
    """The model provider was unavailable or returned a non-JSON model response."""


BedrockClientError = ModelClientError


class JsonModelClient:
    """Shared domain methods; providers only implement generate_json."""

    def generate_json(self, system_prompt: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def _load_prompt(filename: str, fallback: str) -> str:
        prompt_path = Path(__file__).parent / "prompts" / filename
        try:
            prompt = prompt_path.read_text(encoding="utf-8").strip()
        except OSError:
            prompt = ""
        return prompt or fallback

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
                raise ModelClientError("Model output contained no JSON object")
            try:
                return json.JSONDecoder().raw_decode(cleaned[start:])[0]
            except json.JSONDecodeError as error:
                raise ModelClientError(f"Model output contained malformed JSON: {error}") from error

    def evaluate_resume(self, resume: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
        return self.generate_json(
            self._load_prompt("ATS_evaluator.md", "Act as an ATS resume evaluator and return only the ATSReport JSON object."),
            {"resume": resume, "job": job},
        )

    def plan_resume(self, resume: dict[str, Any], job: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
        return self.generate_json(
            self._load_prompt("Resume_planner.md", "Act as a resume rewrite planner and return only the RewritePlan JSON object."),
            {"resume": resume, "job": job, "ats_report": evaluation},
        )

    def rewrite_resume(self, resume: dict[str, Any], job: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        return self.generate_json(
            self._load_prompt("Resume_writer.md", "Act as a truthful resume writer and return only a complete ResumeIR JSON object."),
            {"resume": resume, "job": job, "rewrite_plan": plan},
        )

    def validate_resume(self, authoritative_resume: dict[str, Any], candidate_resume: dict[str, Any]) -> dict[str, Any]:
        return self.generate_json(
            self._load_prompt(
                "Validator.md",
                "Act as a resume truth validator and return only the ValidationReport JSON object.",
            ),
            {"authoritative_resume": authoritative_resume, "candidate_resume": candidate_resume},
        )

    def generate_interview_questions(self, resume: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
        return self.generate_json(
            self._load_prompt(
                "Interview_questions.md",
                "Act as a demanding interview coach and return only the InterviewPrep JSON object.",
            ),
            {"resume": resume, "job": job},
        )

    def validate_interview(self, resume: dict[str, Any], job: dict[str, Any], interview_prep: dict[str, Any]) -> dict[str, Any]:
        return self.generate_json(
            self._load_prompt(
                "Interview_validator.md",
                "Act as an interview answer validator and return only the InterviewValidationReport JSON object.",
            ),
            {"resume": resume, "job": job, "interview_prep": interview_prep},
        )

    def orchestrate(self, state: dict[str, Any]) -> dict[str, Any]:
        return self.generate_json(
            self._load_prompt(
                "Ochestrator.md",
                "Analyze the failed resume workflow and return only a RecoveryDirective JSON object.",
            ),
            state,
        )


class BedrockNovaClient(JsonModelClient):
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
            # Nova returns a response envelope; only the text block crosses into domain code.
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
                raise ModelClientError("Model output was not a JSON object")
            return result
        except ModelClientError:
            raise
        except Exception as error:
            raise ModelClientError(f"Bedrock {self.model_id} request failed: {error}") from error


class OpenAICompatClient(JsonModelClient):
    def __init__(self, model: str | None = None, base_url: str | None = None, api_key: str | None = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def generate_json(self, system_prompt: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise ModelClientError("OPENAI_API_KEY is not configured")
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=True)},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content
            result = self._parse_json(text)
            if not isinstance(result, dict):
                raise ModelClientError("Model output was not a JSON object")
            return result
        except ModelClientError:
            raise
        except Exception as error:
            raise ModelClientError(f"OpenAI-compatible request to {self.model} failed: {error}") from error


def create_model_client() -> JsonModelClient:
    if os.getenv("MODEL_PROVIDER", "bedrock").lower() == "openai":
        return OpenAICompatClient()
    return BedrockNovaClient()
