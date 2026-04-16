
from huggingface_hub import hf_hub_download
from pathlib import Path
from llama_cpp import Llama

PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "oberon"
EMBEDDING_MODEL_NAME = "nomic-embed-text-v1.5.Q2_K.gguf"
EMBEDDING_MODEL_REPO = "nomic-ai/nomic-embed-text-v1.5-GGUF"
CHAT_MODEL_NAME = "gemma-4-E2B-it-Q4_K_M.gguf"
CHAT_MODEL_REPO = "unsloth/gemma-4-E2B-it-GGUF"

class LLMSService:
    def __init__(self):
        self.chat_model = Llama.from_pretrained(
            repo_id=CHAT_MODEL_REPO,
            filename=CHAT_MODEL_NAME,
            n_ctx=4096,
            verbose=False
        )
        self.embed_model = Llama.from_pretrained(
            repo_id=EMBEDDING_MODEL_REPO,
            filename=EMBEDDING_MODEL_NAME,
            n_ctx=4096,
            embedding = True,
            verbose=False
        )

    def create_embedding(self, text):
        embedding = self.embed_model.embed(text)
        print(f"Embedding created for text: '{text}' with length {len(embedding)}")
        return embedding

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
            max_tokens=200
        )

        print(response["choices"][0]["message"]["content"])
        return 
    


