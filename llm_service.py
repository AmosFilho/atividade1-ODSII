
from huggingface_hub import hf_hub_download
from pathlib import Path
from llama_cpp import Llama
from langchain_huggingface.embeddings import HuggingFaceEmbeddings


PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "oberon"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

CHAT_MODEL_NAME = "gemma-4-E2B-it-Q4_K_M.gguf"
CHAT_MODEL_REPO = "unsloth/gemma-4-E2B-it-GGUF"

class LLMService:
    def __init__(self):
        self.chat_model = Llama.from_pretrained(
            repo_id=CHAT_MODEL_REPO,
            filename=CHAT_MODEL_NAME,
            n_ctx=2028,
            verbose=False
        )
        self.embedding = HuggingFaceEmbeddings(model_name = EMBEDDING_MODEL_NAME)
    def create_embedding(self, text):
        embedded_text = self.embedding.embed_query(text)
        print(f"Embedding created for text: '{text}' with length {len(embedded_text)}")
        return embedded_text

    def generate_response(self, prompt):
        # Here you would implement the logic to interact with the LLM model
        # For example, you might call an API or use a library function
        response = self.chat_model.create_chat_completion(
            messages = [
                {
                    "role": "user",
                    "content": prompt
                    
                }
            ],
            max_tokens=2000
        )

        print(response["choices"][0]["message"]["content"])
        return 
    


