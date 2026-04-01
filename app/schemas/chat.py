from pydantic import BaseModel
from uuid import UUID

class ChatRequest(BaseModel):
    query: str
    thread_id: UUID


class ChatResponse(BaseModel):
    response: str
    thread_id: UUID
    report_id: UUID | None = None