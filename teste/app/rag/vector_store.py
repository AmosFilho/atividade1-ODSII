from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any
from uuid import uuid4

import chromadb

from app.core.config import settings
from app.rag.text_splitter import Chunk
from app.schemas.chat import SourceChunk
from app.schemas.documents import DocumentListResponse, IndexedDocument


class ChromaVectorStore:
    def __init__(self, persist_dir: Path | None = None, collection_name: str | None = None) -> None:
        self.persist_dir = persist_dir or settings.vector_store_dir
        self.collection_name = collection_name or settings.chroma_collection
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection: Any = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        source_id: str | None = None,
    ) -> list[str]:
        if not chunks:
            return []
        source_id = source_id or uuid4().hex
        ids = [f"{source_id}:{chunk.metadata['chunk_index']}:{uuid4().hex[:8]}" for chunk in chunks]
        metadatas = [
            {
                "source_id": source_id,
                "filename": str(chunk.metadata.get("filename") or ""),
                "page": int(chunk.metadata["page"]) if chunk.metadata.get("page") is not None else -1,
                "chunk_index": int(chunk.metadata.get("chunk_index") or 0),
                "source_path": str(chunk.metadata.get("source_path") or ""),
            }
            for chunk in chunks
        ]
        self.collection.add(
            ids=ids,
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return ids

    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[SourceChunk]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        chunks: list[SourceChunk] = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            page = metadata.get("page")
            page = int(page) if page is not None and int(page) > 0 else None
            chunks.append(
                SourceChunk(
                    id=chunk_id,
                    source_id=str(metadata.get("source_id") or ""),
                    filename=str(metadata.get("filename") or ""),
                    page=page,
                    chunk_index=int(metadata.get("chunk_index") or 0),
                    text=text,
                    score=1 - float(distance) if distance is not None else None,
                )
            )
        return chunks

    def list_documents(self) -> DocumentListResponse:
        data = self.collection.get(include=["metadatas"])
        counts: dict[str, dict[str, str | int]] = defaultdict(lambda: {"filename": "", "chunks": 0})
        for metadata in data.get("metadatas", []):
            source_id = str(metadata.get("source_id") or "")
            if not source_id:
                continue
            counts[source_id]["filename"] = str(metadata.get("filename") or "")
            counts[source_id]["chunks"] = int(counts[source_id]["chunks"]) + 1

        documents = [
            IndexedDocument(
                source_id=source_id,
                filename=str(value["filename"]),
                chunks=int(value["chunks"]),
            )
            for source_id, value in sorted(counts.items(), key=lambda item: item[1]["filename"])
        ]
        return DocumentListResponse(documents=documents)

    def delete_document(self, source_id: str) -> int:
        data = self.collection.get(where={"source_id": source_id})
        ids = data.get("ids", [])
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)

    def clear(self) -> int:
        data = self.collection.get()
        ids = data.get("ids", [])
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)
