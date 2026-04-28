from app.rag.document_loader import LoadedDocument
from app.rag.text_splitter import ParagraphTextSplitter


def test_splitter_keeps_metadata_and_limits_chunk_size() -> None:
    document = LoadedDocument(
        text="Paragrafo inicial com regra importante.\n\n" + "palavra " * 120,
        metadata={"filename": "protocolo_endoscopia.md", "page": None, "source_path": "protocolo_endoscopia.md"},
    )
    splitter = ParagraphTextSplitter(chunk_size=120, chunk_overlap=20)

    chunks = splitter.split_documents([document])

    assert len(chunks) > 1
    assert chunks[0].metadata["filename"] == "protocolo_endoscopia.md"
    assert chunks[0].metadata["chunk_index"] == 0
    assert all(len(chunk.text) <= 140 for chunk in chunks)
