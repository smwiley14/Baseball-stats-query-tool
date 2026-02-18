import pandas as pd
from langchain_core.messages import BaseMessage
# from loguru import logger
from sqlalchemy import text

from backend.agent.state import State
from backend.database.db_connect import DBConnector

def validate_sql(query: str, db_connector: DBConnector):
    pass

def format_response_to_user(response: str):
    pass

def format_response_to_agent(response: str):
    pass


def execute_sql(query: str, db_connector: DBConnector):
    """Execute a SQL query and return results."""
    try:
        engine = db_connector.get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(query))
            if result.returns_rows:
                # Fetch all rows
                rows = result.fetchall()
                columns = result.keys()
                # Convert to list of dicts
                data = [dict(zip(columns, row)) for row in rows]
                return {
                    "status": "success",
                    "data": data,
                    "row_count": len(data)
                }
            else:
                return {
                    "status": "success",
                    "data": None,
                    "message": "Query executed successfully (no rows returned)"
                }
    except Exception as e:
        return {
            "status": "failure",
            "error": str(e)
        }


def get_chat_history(messages: list[BaseMessage], n: int=10):
    return "\n".join(
        [f"{msg.type.upper()}: {msg.content}" for msg in messages[-n:]]
    )

# def format_sql_execution_result(result: pd.DataFrame):
#     return result.to_dict(orient="records")
