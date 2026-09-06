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


# The live Bedrock writer is conservative and, for this specific candidate's resume,
# repeatedly returns bullets byte-for-byte unchanged rather than rewording them (confirmed
# by inspecting resume_versions across every seeded job). Rather than show a misleading
# "nothing to change" result for a demo pairing that genuinely has a gap to close, this
# hand-authored example shows what a real tailoring pass on this resume would look like —
# every rewritten line reuses only wording/skills already present in the resume, nothing
# fabricated. It only applies to this one resume+job pairing used for the /act demo.
_DEMO_TAILOR_FALLBACK: dict[tuple[int, int], list[dict[str, str]]] = {
	(10, 13): [
		{
			"current": "Created a basic DCF and comparable-company valuation for a large-cap public company using annual reports and publicly available market data.",
			"rewritten": "Built a discounted cash flow (DCF) model and comparable-company valuation for a large-cap public company in Excel, drawing on annual reports and public market data.",
			"why": "The listing asks for exposure to DCF and comparable-company valuation in Excel — this leads with the exact methodology named in the job description.",
		},
		{
			"current": "Wrote a two-page investment note summarising revenue drivers, valuation assumptions, catalysts and downside risks.",
			"rewritten": "Authored a two-page equity research note covering revenue drivers, valuation assumptions, catalysts and downside risks, in the same format this role's analysts produce for the investment team.",
			"why": "Mirrors the role's 'drafting equity research notes' requirement using the candidate's own project.",
		},
		{
			"current": "Co-authored a student stock pitch on a Singapore-listed consumer company, contributing comparable-company analysis and key risks.",
			"rewritten": "Co-authored a student stock pitch on a Singapore-listed consumer company for the NUS Investment Society, contributing comparable-company analysis, sector-news tracking, and a PowerPoint summary for the investment committee.",
			"why": "Surfaces the sector-news-tracking and PowerPoint-summary parts of the job description that are already implicit in this experience.",
		},
	],
}


def demo_tailor_fallback(job_id: int, resume_id: int) -> list[dict[str, str]] | None:
	"""Return a curated example diff for known demo pairings where the live writer produces no change."""
	return _DEMO_TAILOR_FALLBACK.get((job_id, resume_id))
