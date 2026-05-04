from __future__ import annotations

from dataclasses import dataclass

from app.rag.document_loader import LoadedDocument


@dataclass(frozen=True)
class Chunk:
    text: str
    metadata: dict[str, str | int | None]


class ParagraphTextSplitter:
    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 150) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap precisa ser menor que chunk_size.")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents: list[LoadedDocument]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for document in documents:
            for chunk_index, text in enumerate(self._split_text(document.text)):
                metadata = dict(document.metadata)
                metadata["chunk_index"] = chunk_index
                chunks.append(Chunk(text=text, metadata=metadata))
        return chunks

    def _split_text(self, text: str) -> list[str]:
        paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            if len(paragraph) > self.chunk_size:
                if current:
                    chunks.append(current.strip())
                    current = ""
                chunks.extend(self._split_long_paragraph(paragraph))
                continue

            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                chunks.append(current.strip())
                current = self._with_overlap(chunks[-1], paragraph)

        if current:
            chunks.append(current.strip())

        return chunks

    def _split_long_paragraph(self, paragraph: str) -> list[str]:
        words = paragraph.split()
        chunks: list[str] = []
        current_words: list[str] = []
        current_len = 0

        for word in words:
            extra = len(word) + (1 if current_words else 0)
            if current_words and current_len + extra > self.chunk_size:
                current_text = " ".join(current_words)
                chunks.append(current_text)
                overlap_words = self._tail_words(current_text)
                current_words = overlap_words + [word]
                current_len = len(" ".join(current_words))
            else:
                current_words.append(word)
                current_len += extra

        if current_words:
            chunks.append(" ".join(current_words))
        return chunks

    def _with_overlap(self, previous: str, next_paragraph: str) -> str:
        overlap = previous[-self.chunk_overlap :].strip()
        return f"{overlap}\n\n{next_paragraph}".strip()

    def _tail_words(self, text: str) -> list[str]:
        tail = text[-self.chunk_overlap :].strip()
        return tail.split()

