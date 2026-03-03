from pydantic import BaseModel
from typing import Optional, Any


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: Optional[list] = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    table_data: Optional[list[dict[str, Any]]] = None
    supplemental_data: Optional[dict[str, Any]] = None
    summary: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class CancelRequest(BaseModel):
    session_id: str


class CancelResponse(BaseModel):
    status: str
    session_id: str
