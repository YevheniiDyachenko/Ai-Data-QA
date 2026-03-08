from __future__ import annotations

import re

from ai_data_qa.errors import SQLValidationError

_BLOCKED_PATTERN = re.compile(r"\b(DROP|DELETE|UPDATE|INSERT|MERGE|ALTER|TRUNCATE|CREATE)\b", re.IGNORECASE)
_SELECT_PATTERN = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
_LIMIT_PATTERN = re.compile(r"\bLIMIT\s+(\d+)\b", re.IGNORECASE)


def validate_select_query(sql: str, max_limit: int = 10000) -> str:
    """Validate SQL safety before execution.

    Rules:
    - SELECT-only queries
    - deny dangerous write/ddl statements
    - enforce LIMIT and maximum limit value
    """
    normalized = sql.strip().rstrip(";")
    if not normalized:
        raise SQLValidationError("SQL query cannot be empty")

    if not _SELECT_PATTERN.match(normalized):
        raise SQLValidationError("Only SELECT queries are allowed", sql=normalized)

    blocked = _BLOCKED_PATTERN.search(normalized)
    if blocked:
        raise SQLValidationError("Blocked SQL keyword detected", keyword=blocked.group(1), sql=normalized)

    limit_match = _LIMIT_PATTERN.search(normalized)
    if not limit_match:
        normalized = f"{normalized} LIMIT {max_limit}"
    else:
        limit_value = int(limit_match.group(1))
        if limit_value > max_limit:
            raise SQLValidationError(
                "LIMIT exceeds allowed maximum",
                limit=limit_value,
                allowed=max_limit,
                sql=normalized,
            )

    return normalized
