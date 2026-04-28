from app.core.config import settings
from app.rag.embeddings import EmbeddingModel
from app.rag.vector_store import ChromaVectorStore
from app.schemas.chat import SourceChunk


class Retriever:
    def __init__(self, embeddings: EmbeddingModel, vector_store: ChromaVectorStore) -> None:
        self.embeddings = embeddings
        self.vector_store = vector_store

    def retrieve(self, question: str, top_k: int | None = None) -> list[SourceChunk]:
        query_embedding = self.embeddings.embed_query(question)
        return self.vector_store.similarity_search(query_embedding, top_k or settings.top_k)

