"""Small, dependency-free guard for generated read-only SQL."""

import re


class SqlSafetyError(ValueError):
    """Raised when generated SQL is outside the read-only query contract."""


_WRITE_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|GRANT|REVOKE|CALL|EXEC|SET|LOAD|LOCK|UNLOCK)\b",
    re.IGNORECASE,
)
_COMMENT = re.compile(r"(--[^\n]*|/\*.*?\*/)", re.DOTALL)


def assert_read_only_sql(sql: str) -> str:
    """Return normalized SQL or raise when it is unsafe to explain/execute."""
    if not isinstance(sql, str) or not sql.strip():
        raise SqlSafetyError("SQL 为空")
    normalized = _COMMENT.sub(" ", sql).strip()
    if ";" in normalized.rstrip(";"):
        raise SqlSafetyError("不允许执行多条 SQL")
    if not re.match(r"^(SELECT|WITH)\b", normalized, re.IGNORECASE):
        raise SqlSafetyError("只允许 SELECT 或 WITH 查询")
    if _WRITE_KEYWORDS.search(normalized):
        raise SqlSafetyError("检测到不允许的写操作或管理操作")
    return normalized.rstrip(";").strip()
