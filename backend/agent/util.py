import logging
import re

from langchain_core.messages import BaseMessage
from sqlalchemy import text

from agent.state import State
from config import UNSAFE_SQL_KEYWORDS
from database.db_connect import DBConnector

logger = logging.getLogger(__name__)


class UnsafeSQLError(ValueError):
    """Raised when a SQL query contains disallowed keywords."""


def validate_sql(query: str, db_connector: DBConnector | None = None) -> None:
    """Raise UnsafeSQLError if *query* contains any disallowed SQL keywords.

    Checks are case-insensitive and use word-boundary matching so that column
    names like 'update_date' do not trigger a false positive.

    Args:
        query: The SQL string to validate.
        db_connector: Unused — kept for API compatibility.

    Raises:
        UnsafeSQLError: If a disallowed keyword is found.
    """
    for keyword in UNSAFE_SQL_KEYWORDS:
        # \b ensures we match the whole word, not a substring.
        if re.search(rf"\b{re.escape(keyword)}\b", query, re.IGNORECASE):
            raise UnsafeSQLError(
                f"SQL query contains disallowed keyword: '{keyword}'. "
                "Only SELECT queries are permitted."
            )


def execute_sql(query: str, db_connector: DBConnector):
    """Execute a SQL query and return results.

    The query is validated against UNSAFE_SQL_KEYWORDS before execution.
    Any validation or database errors are caught and returned as a failure
    dict so the caller can decide how to surface them to the user.
    """
    try:
        validate_sql(query, db_connector)
    except UnsafeSQLError as e:
        logger.warning("Blocked unsafe SQL query: %s", e)
        return {
            "status": "failure",
            "error": str(e),
        }

    try:
        engine = db_connector.get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(query))
            if result.returns_rows:
                rows = result.fetchall()
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in rows]
                return {
                    "status": "success",
                    "data": data,
                    "row_count": len(data),
                }
            else:
                return {
                    "status": "success",
                    "data": None,
                    "message": "Query executed successfully (no rows returned)",
                }
    except Exception as e:
        logger.exception("SQL execution error")
        return {
            "status": "failure",
            # Return a sanitised message — callers must not forward str(e) to users.
            "error": "Database error during query execution.",
        }


def get_chat_history(messages: list[BaseMessage], n: int=10):
    return "\n".join(
        [f"{msg.type.upper()}: {msg.content}" for msg in messages[-n:]]
    )

