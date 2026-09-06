import json


def row_to_dict(row):
    return dict(row) if row is not None else None


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def dumps(value):
    return json.dumps(value) if value is not None else None


def loads(value):
    return json.loads(value) if value is not None else None
