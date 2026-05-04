from app.rag.document_loader import DocumentLoader


def test_load_txt_document(tmp_path) -> None:
    path = tmp_path / "documento.txt"
    path.write_text("Linha 1\n\n\nLinha 2", encoding="utf-8")

    documents = DocumentLoader().load(path)

    assert len(documents) == 1
    assert documents[0].text == "Linha 1\n\nLinha 2"
    assert documents[0].metadata["filename"] == "documento.txt"

