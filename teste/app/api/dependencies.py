from functools import lru_cache

from app.rag.pipeline import RAGPipeline


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RAGPipeline:
    return RAGPipeline()

