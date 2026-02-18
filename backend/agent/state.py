from pydantic import BaseModel
from typing import Annotated, Literal, Any
from langgraph.graph.message import add_messages, BaseMessage

class State(BaseModel):
    """State for the NL2SQL agent."""
    user_query: str | None = None
    messages: Annotated[list[BaseMessage], add_messages]
    sql_query: str | None = None
    sql_generation_status: Literal["success", "failure"] | None = None
    sql_execution_result: dict[str, Any] | None = None
    sql_execution_status: Literal["success", "failure"] | None = None
    # user_query: str | None = None
    # user_intent: Literal["sql", "chat"] | None = None
    # sql_query: str | None = None
    # sql_explanation: str | None = None
    # sql_execution_result: dict[str, Any] | None = None
    # sql_execution_analysis: str | None = None
    # sql_safety_status: Literal["safe", "unsafe"] | None = None
    # sql_syntax_status: Literal["valid", "invalid"] | None = None
    # user_feedback_status: Literal["approved", "rejected"] | None = None
    # sql_execution_status: Literal["success", "failure"] | None = None
