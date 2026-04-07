from pydantic import BaseModel, Field
from typing import Optional, Any

# Absolute maximum query length accepted by the API.
# Nginx already blocks bodies over 8 KB, but this is a second layer of defence
# inside the application itself (e.g. if Nginx is bypassed or misconfigured).
_MAX_MESSAGE_LENGTH = 2_000


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=_MAX_MESSAGE_LENGTH,
        description="Natural-language baseball stats query (max 2 000 characters).",
    )
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
