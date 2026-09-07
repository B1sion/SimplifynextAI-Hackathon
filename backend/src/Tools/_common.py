import json
import sqlite3
from typing import Any


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def rows_to_dicts(rows) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def dumps(value: Any) -> str | None:
    return json.dumps(value) if value is not None else None


def loads(value: str | None) -> Any:
    return json.loads(value) if value is not None else None
