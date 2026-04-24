from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from langchain_core.documents import Document
import json
import os

chunk_size = 1000
chunk_overlap = 200
docs_text_separators=[
            "\nArt.",
            "\n§",
            "\n",
            ". ",
            " "
        ]
def load_pdf(path:str):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"File not found: {path}"
        )
    loader = PyPDFLoader(path)
    docs = loader.load()
    if not docs:
        raise ValueError(
            f"No documents found in PDF: {path}"
        )
    print(f"len(docs): {len(docs)} página(s) carregadas do PDF.")
    return docs

def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap,
        separators=docs_text_separators
    )
    chunks = splitter.split_documents(docs)
    for chunk in chunks:
        page = chunk.metadata.get("page_label", "N/A")

        chunk.page_content = f"[Página {page}]\n{chunk.page_content}"

    return chunks


def process_pdf(
    pdf_path: str
) -> list[Document]:

    print(f"Processando {pdf_path}")

    docs = load_pdf(pdf_path)

    chunks = split_documents(docs)

    document_name = Path(pdf_path).stem

    for i, chunk in enumerate(chunks):

        page = chunk.metadata.get(
            "page",
            chunk.metadata.get(
                "page_label",
                "N/A"
            )
        )

        chunk.metadata.update({
            "document_name": document_name,
            "source_file": pdf_path,
            "page_number": page,
            "chunk_index": i
        })

    return chunks

def load_and_split_folder(
    folder_path: str
) -> list[Document]:

    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(
            f"Pasta não encontrada: {folder_path}"
        )

    pdf_files = list(
        folder.rglob("*.pdf")
    )

    if not pdf_files:
        raise ValueError(
            "Nenhum PDF encontrado."
        )

    all_chunks = []

    for pdf_path in pdf_files:

        chunks = process_pdf(
            str(pdf_path)
        )

        all_chunks.extend(chunks)

    print(
        f"Total de chunks: {len(all_chunks)}"
    )

    return all_chunks
