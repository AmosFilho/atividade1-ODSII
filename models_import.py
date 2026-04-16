
from huggingface_hub import hf_hub_download

PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "oberon"
EMBEDDING_MODEL = "models/nomic-embed-text-v1.5.gguf"
CHAT_MODEL = "models/gemma-4-E2B-it-Q4_K_M.gguf"

model_path = hf_hub_download(
    repo_id="nomic-ai/nomic-embed-text-v1.5-GGUF",
    filename="nomic-embed-text-v1.5.Q4_K_M.gguf"
)

print(model_path)
#https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF
