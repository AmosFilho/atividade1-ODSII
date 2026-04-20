from langchain_chroma import Chroma
from langchain_core.documents import Document
from llama_cpp import Llama
from langchain_community.embeddings import LlamaCppEmbeddings
import os
from extract_documents import load_pdf, split_documents

from llm_service import LLMService

PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "oberon"

def load_or_create_index_chroma(llm_service: LLMService):
    docs = load_pdf("documents/ECA2021_Digital.pdf")
    chunks = split_documents(docs)
    print(f"Total de chuncks: {len(chunks)}, conteúdo do primeiro chunck: {chunks[0].page_content[:200]}")
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=llm_service.embedding,
        persist_directory=PERSIST_DIR
    )
    print(f"Chuncks: {chunks}")
    if vector_store._collection.count() == 0:
        print("Creating new index and adding documents...")

        vector_store.add_documents(chunks)  # resolve tudo

        vector_store.persist()

    else:
        print("Reusing existing index...")
    #embeddings = llm_service.embedding.embed_documents(chuncks)

        

    return vector_store


class IndexService:
    def __init__(self, llm_service, persist_dir: str, collection_name: str):
        self.llm_service = llm_service
        self.persist_dir = persist_dir
        self.collection_name = collection_name

        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.llm_service.embedding,
            persist_directory=self.persist_dir
        )
    
    def _load_documents(self) -> list[Document]:
        docs = load_pdf("documents/ECA2021_Digital.pdf")
        chunks = split_documents(docs)

        print(f"Total de chunks: {len(chunks)}")
        print(f"Primeiro chunk: {chunks[0].page_content[:200]}")

        return chunks

    def _generate_ids(self, documents: list[Document]) -> list[str]:
        return [f"doc_{i}" for i in range(len(documents))]

    def initialize(self):
        """
        Cria ou atualiza o índice
        """

        documents = self._load_documents()

        existing_count = self.vector_store._collection.count()

        if existing_count == 0:
            print("Criando nova coleção e indexando documentos...")

            ids = self._generate_ids(documents)

            self.vector_store.add_documents(documents, ids=ids)

        else:
            print(f"Coleção já existe com {existing_count} documentos")

            # Aqui você pode implementar lógica de atualização
            print("Pulando reindexação (evitando duplicação)")

    def get_retriever(self, k: int):
        return self.vector_store.as_retriever(search_kwargs={"k": k})

    def similarity_search(self, query: str, k: int):
        return self.vector_store.similarity_search(query, k=k)