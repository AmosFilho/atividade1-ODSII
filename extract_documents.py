from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
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

