
from huggingface_hub import hf_hub_download
from pathlib import Path
from llama_cpp import Llama
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
import logging
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import CrossEncoder

# Configurações de Log
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# evita duplicação
logger.propagate = False

# handler para terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# formato bonito
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
console_handler.setFormatter(formatter)

# evita adicionar múltiplos handlers
if not logger.handlers:
    logger.addHandler(console_handler)

PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "oberon"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

CHAT_MODEL_NAME = "gemma-4-E2B-it-Q4_K_M.gguf"
CHAT_MODEL_REPO = "unsloth/gemma-4-E2B-it-GGUF"

RERANKING_MODEL_NAME = "Qwen/Qwen3-Reranker-0.6B"

class LLMService:
    def __init__(self):
        self.chat_model = Llama.from_pretrained(
            repo_id=CHAT_MODEL_REPO,
            filename=CHAT_MODEL_NAME,
            n_ctx=8192,
            verbose=False
        )
        self.embedding = HuggingFaceEmbeddings(model_name = EMBEDDING_MODEL_NAME)
        self.rerank_tokenizer = AutoTokenizer.from_pretrained(
            RERANKING_MODEL_NAME
        )

        self.rerank_model = CrossEncoder(
            RERANKING_MODEL_NAME,
            device = "cpu",
            max_length=512
        )
    def create_embedding(self, text):
        embedded_text = self.embedding.embed_query(text)
        print(f"Embedding created for text: '{text}' with length {len(embedded_text)}")
        return embedded_text
    
    def rerank(self, query: str, documents: list, top_n: int = 3):
        """
        Usa o CrossEncoder do Qwen para reordenar os documentos.
        """
        if not documents:
            return []

        # 1. Preparar os textos (Extrai 'page_content' se for objeto do LangChain)
        doc_texts = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in documents
        ]


        # 🔹 LOG ANTES DO RERANK
        logger.info("\n========== 🔎 BEFORE RERANK ==========")
        for i, (doc, text) in enumerate(zip(documents, doc_texts)):
            preview = text.replace("\n", " ")
            logger.info(f"#{i+1} | {preview}")
            print(doc.metadata.get("document_name"))

        # 2. Criar pares (query, passagem)
        pairs = [[query, text] for text in doc_texts]

        # 3. Predição de scores (O CrossEncoder lida com o padding automaticamente)
        # predict retorna uma lista de floats
        scores = self.rerank_model.predict(pairs)

        # 4. Associar documentos originais aos scores e ordenar
        ranked_results = sorted(
            zip(documents, scores, doc_texts),
            key=lambda x: x[1],
            reverse=True
        )

        logger.info("\n========== 🚀 AFTER RERANK ==========")
        for i, (doc, score, text) in enumerate(ranked_results[:top_n]):
            preview = text[:200].replace("\n", " ")
            logger.info(f"#{i+1} | Score: {score:.4f} | {preview}")

            # opcional: metadata (muito útil)
            #if hasattr(doc, "metadata"):
                #logger.info(f"    metadata: {doc.metadata}")

        logger.info("=====================================\n")


        # Log para debug
        logger.info(f"Rerank concluído. Melhor score: {ranked_results[0][1]:.4f}")

        # Retornar apenas os top_n documentos originais
        return [doc for doc, score, text in ranked_results[:top_n]]

    def ask(self, system_prompt: str, user_query: str, max_tokens: int = 2000, temperature: float = 0.7):
        """
        Método unificado para gerar respostas do Chat.
        Encapsula a complexidade do chat_model.
        """
        try:
            response = self.chat_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Retorna apenas o texto da resposta
            return response["choices"][0]["message"]["content"]
        
        except Exception as e:
            print(f"Erro ao gerar resposta do LLM: {e}")
            return "Desculpe, ocorreu um erro ao processar sua solicitação."
    


