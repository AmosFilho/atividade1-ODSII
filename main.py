
from llama_cpp import Llama
from langchain_community.chat_models import ChatLlamaCpp
from langchain_core.messages import SystemMessage, HumanMessage
from index_service import load_or_create_index_chroma
from llm_service import LLMSService

import os
import warnings
import sys
'''
os.environ["LLAMA_LOG_LEVEL"] = "ERROR"
warnings.filterwarnings("ignore")
sys.stderr = open(os.devnull, 'w')
'''
MODEL_ID = "gemma-4-E2B-it-BF16.gguf"
REPO_ID = "unsloth/gemma-4-E2B-it-GGUF"
MODEL_PATH = "models/gemma-4-E2B-it-Q4_K_M.gguf"

def main():
    
    llm = LLMSService()

    llm.generate_response("Olá, qual é a capital da França?")
    llm.create_embedding("Olá, tudo bem?")

    return 

if __name__ == "__main__":
    main()

#TODO Ignorar o modelo baixado +  Adicionar o git ignore + ignorar a pasta do modelo + Adicionar o modelo baixado no readme + Adicionar o modelo baixado no requirements.txt