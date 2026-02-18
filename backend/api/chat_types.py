from pydantic import BaseModel
from typing import Optional, Any


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: Optional[list] = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    metadata: Optional[dict[str, Any]] = None