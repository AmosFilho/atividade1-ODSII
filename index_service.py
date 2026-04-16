from langchain_chroma import Chroma
from langchain_core.documents import Document
from llama_cpp import Llama
from langchain_community.embeddings import LlamaCppEmbeddings
import os

from llm_service import LLMSService

PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "oberon"

def load_or_create_index_chroma(documents: list[Document], llm_service: LLMSService):

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=llm_service.create_embedding,
        persist_directory=PERSIST_DIR
    )

    # Se estiver vazio, adiciona documentos
    if vector_store._collection.count() == 0:
        print("Creating new Chroma index...")
        vector_store.add_documents(documents)
    else:
        print("Reusing existing Chroma index...")

    return vector_store