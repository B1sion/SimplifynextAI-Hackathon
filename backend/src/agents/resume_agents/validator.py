from typing import Any
from typing import Protocol

from .contracts import ResumeIR, ValidationReport


class ValidationModelClient(Protocol):
    def validate_resume(self, authoritative_resume: dict[str, Any], candidate_resume: dict[str, Any]) -> dict[str, Any]: ...


def _validate(model, value):
    return model.model_validate(value) if hasattr(model, "model_validate") else model.parse_obj(value)


def _normalize_report(result: dict[str, Any]) -> dict[str, Any]:
    """Normalize only the agent response shape; never decide truth in Python."""
    normalized = dict(result)
    additions = normalized.get("unsupported_additions") or []
    normalized["unsupported_additions"] = [
        item if isinstance(item, dict) else {
            "category": "agent_reported_issue",
            "claim": str(item),
            "reason": "The truth-validation agent reported this claim as unsupported.",
        }
        for item in additions
    ]
    normalized["changed_dates"] = [str(item) for item in (normalized.get("changed_dates") or [])]
    normalized["inflated_titles"] = [str(item) for item in (normalized.get("inflated_titles") or [])]
    return normalized


def validate_resume(
    authoritative_resume: ResumeIR | dict[str, Any],
    candidate_resume: ResumeIR | dict[str, Any],
    model_client: ValidationModelClient,
) -> ValidationReport:
    """Ask the truth-validation agent whether the candidate is supported.

    This layer intentionally performs no Python claim matching or structural
    content judgment. The validation agent is the authority for subjective
    truthfulness decisions; ResumeIR validation only checks the response shape.
    """
    authoritative = _validate(ResumeIR, authoritative_resume)
    candidate = _validate(ResumeIR, candidate_resume)
    result = model_client.validate_resume(authoritative.model_dump(), candidate.model_dump())
    return _validate(ValidationReport, _normalize_report(result))