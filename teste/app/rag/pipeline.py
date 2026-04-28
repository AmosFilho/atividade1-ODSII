from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.rag.document_loader import DocumentLoader
from app.rag.embeddings import EmbeddingModel
from app.rag.llm import OllamaLLM
from app.rag.retriever import Retriever
from app.rag.text_splitter import ParagraphTextSplitter
from app.rag.triage import build_triage_answer, triage_question
from app.rag.vector_store import ChromaVectorStore
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.documents import DocumentListResponse, IngestResponse


class RAGPipeline:
    def __init__(self) -> None:
        self.loader = DocumentLoader()
        self.splitter = ParagraphTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.embeddings = EmbeddingModel()
        self.vector_store = ChromaVectorStore()
        self.retriever = Retriever(self.embeddings, self.vector_store)
        self.llm = OllamaLLM()

    def ingest_file(self, path: Path, original_filename: str | None = None) -> IngestResponse:
        documents = self.loader.load(path, original_filename=original_filename)
        chunks = self.splitter.split_documents(documents)
        if not chunks:
            raise ValueError("Nao foi possivel extrair texto util do documento.")

        embeddings = self.embeddings.embed_texts([chunk.text for chunk in chunks])
        source_id = uuid4().hex
        self.vector_store.add_chunks(chunks, embeddings, source_id=source_id)
        return IngestResponse(
            message="Documento indexado com sucesso.",
            chunks_indexed=len(chunks),
            document_ids=[source_id],
        )

    def ask(self, request: ChatRequest) -> ChatResponse:
        triage = triage_question(request.question)
        triage_answer = build_triage_answer(triage)
        if triage_answer is not None:
            return ChatResponse(answer=triage_answer, sources=[], triage=triage)

        sources = self.retriever.retrieve(request.question, request.top_k)
        if not sources:
            return ChatResponse(
                answer="Nao encontrei documentos indexados suficientes para responder.",
                sources=[],
                triage=triage,
            )
        answer = self.llm.generate(request.question, sources)
        if triage.action == "operacional_com_confirmacao":
            answer = (
                f"{answer}\n\n"
                "Como sua situacao envolve preparo incompleto, divergencia ou uma condicao operacional "
                "que pode afetar o procedimento, confirme com a equipe da clinica antes de seguir."
            )
        return ChatResponse(answer=answer, sources=sources, triage=triage)

    def list_documents(self) -> DocumentListResponse:
        return self.vector_store.list_documents()

    def delete_document(self, source_id: str) -> int:
        return self.vector_store.delete_document(source_id)

    def clear(self) -> int:
        return self.vector_store.clear()
