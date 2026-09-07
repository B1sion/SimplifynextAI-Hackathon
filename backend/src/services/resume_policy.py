import re
from typing import Any


def gpa_meets_first_class_threshold(value: Any) -> bool:
    match = re.search(
        r"(?P<score>\d+(?:\.\d+)?)\s*(?:/|out of)\s*(?P<scale>\d+(?:\.\d+)?)",
        str(value or ""),
        re.IGNORECASE,
    )
    if not match:
        return True
    score = float(match.group("score"))
    scale = float(match.group("scale"))
    return (scale == 5 and score >= 4.5) or (scale == 4 and score >= 3.5)


def omit_low_gpa(education: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for item in education:
        result = dict(item)
        for key in ("gpa", "GPA", "grade"):
            if key in result and result[key] and not gpa_meets_first_class_threshold(result[key]):
                result.pop(key)
        cleaned.append(result)
    return cleaned