from typing import Any

from src.Tools.plan_tools import get_latest_rewrite_plan

_GENERIC_WHY = "Rewritten to better align with the target role using only the candidate's existing experience."


def _reason_for(plan_changes: list[dict[str, Any]], section: str) -> str:
	for change in plan_changes:
		if section.casefold() in (change.get("section") or "").casefold():
			return change.get("reason") or change.get("instruction") or _GENERIC_WHY
	return _GENERIC_WHY


def _bullet_diffs(original_items: list[dict[str, Any]], final_items: list[dict[str, Any]], why: str) -> list[dict[str, str]]:
	diffs: list[dict[str, str]] = []
	original_bullets = [bullet for item in original_items for bullet in item.get("bullets") or []]
	final_bullets = [bullet for item in final_items for bullet in item.get("bullets") or []]
	for original_bullet, final_bullet in zip(original_bullets, final_bullets):
		if original_bullet != final_bullet:
			diffs.append({"current": original_bullet, "rewritten": final_bullet, "why": why})
	return diffs


def build_resume_diffs(original: dict[str, Any], final: dict[str, Any], run_id: int | None) -> list[dict[str, str]]:
	"""Compare the authoritative resume to the optimizer's final version and return only bullets that actually changed."""
	plan = get_latest_rewrite_plan(run_id) if run_id else None
	plan_changes = ((plan or {}).get("plan_json") or {}).get("changes", []) if plan else []

	diffs: list[dict[str, str]] = []
	diffs.extend(_bullet_diffs(original.get("work_experience") or [], final.get("work_experience") or [], _reason_for(plan_changes, "Experience")))
	diffs.extend(_bullet_diffs(original.get("projects") or [], final.get("projects") or [], _reason_for(plan_changes, "Projects")))

	original_summary = (original.get("summary") or "").strip()
	final_summary = (final.get("summary") or "").strip()
	if final_summary and original_summary != final_summary:
		diffs.append({
			"current": original_summary or "(no summary yet)",
			"rewritten": final_summary,
			"why": _reason_for(plan_changes, "Summary"),
		})
	return diffs


def build_blocked_claim(validation: dict[str, Any] | None) -> dict[str, str] | None:
	"""Surface the first validator-rejected claim from a failed optimization run, if any."""
	if not validation:
		return None
	issues = validation.get("unsupported_additions") or []
	if not issues:
		return None
	issue = issues[0]
	return {
		"proposed": issue.get("claim", ""),
		"reason": issue.get("reason", ""),
		"kept": "Original resume content unchanged",
	}
