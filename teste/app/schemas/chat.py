from pydantic import BaseModel, Field


class TriageDecision(BaseModel):
    action: str
    reason: str
    requires_human: bool = False
    is_emergency: bool = False


class SourceChunk(BaseModel):
    id: str
    source_id: str
    filename: str
    page: int | None = None
    chunk_index: int
    text: str
    score: float | None = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, examples=["Quais documentos preciso enviar?"])
    top_k: int | None = Field(default=None, ge=1, le=10)


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    triage: TriageDecision | None = None
