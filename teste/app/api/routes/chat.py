from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_rag_pipeline
from app.rag.pipeline import RAGPipeline
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def ask_question(
    request: ChatRequest,
    rag: RAGPipeline = Depends(get_rag_pipeline),
) -> ChatResponse:
    try:
        return rag.ask(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

