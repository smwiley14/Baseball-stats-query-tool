from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str
    

class ChatResponse(BaseModel):
    message: str
    history: list[dict[str, str]]
    sources: list[str]
    answer: str
    answer_sources: list[str]
    answer_sources_text: str
    answer_sources_text_list: list[str]
    answer_sources_text_list_list: list[list[str]]