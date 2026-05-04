from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader


@dataclass(frozen=True)
class LoadedDocument:
    text: str
    metadata: dict[str, str | int | None]


class DocumentLoader:
    def load(self, path: Path, original_filename: str | None = None) -> list[LoadedDocument]:
        suffix = path.suffix.lower()
        filename = original_filename or path.name

        if suffix == ".pdf":
            return self._load_pdf(path, filename)
        if suffix in {".txt", ".md", ".markdown"}:
            return [self._load_text(path, filename)]
        if suffix in {".html", ".htm"}:
            return [self._load_html(path, filename)]

        raise ValueError(f"Formato nao suportado: {suffix}")

    def _load_pdf(self, path: Path, filename: str) -> list[LoadedDocument]:
        reader = PdfReader(str(path))
        documents: list[LoadedDocument] = []
        for index, page in enumerate(reader.pages, start=1):
            raw_text = page.extract_text() or ""
            text = clean_text(raw_text)
            if text:
                documents.append(
                    LoadedDocument(
                        text=text,
                        metadata={"filename": filename, "page": index, "source_path": str(path)},
                    )
                )
        return documents

    def _load_text(self, path: Path, filename: str) -> LoadedDocument:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return LoadedDocument(
            text=clean_text(text),
            metadata={"filename": filename, "page": None, "source_path": str(path)},
        )

    def _load_html(self, path: Path, filename: str) -> LoadedDocument:
        html = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        return LoadedDocument(
            text=clean_text(text),
            metadata={"filename": filename, "page": None, "source_path": str(path)},
        )


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

