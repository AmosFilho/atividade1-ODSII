
from llama_cpp import Llama
from langchain_community.chat_models import ChatLlamaCpp
from langchain_core.messages import SystemMessage, HumanMessage
from llm_service import LLMService
from index_service import IndexService

import os
import warnings
import sys
from chat_service import ChatService
from evaluation_results import RAGEvaluator

'''
os.environ["LLAMA_LOG_LEVEL"] = "ERROR"
warnings.filterwarnings("ignore")
sys.stderr = open(os.devnull, 'w')
'''
MODEL_ID = "gemma-4-E2B-it-BF16.gguf"
REPO_ID = "unsloth/gemma-4-E2B-it-GGUF"
MODEL_PATH = "models/gemma-4-E2B-it-Q4_K_M.gguf"
PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "oberon"

def main():
    
    llm = LLMService()

    #llm.generate_response("Olá, qual é a capital da França?")
    #llm.create_embedding("Olá, tudo bem?")

    storage_service = IndexService(
        llm_service=llm,
        persist_dir=PERSIST_DIR,
        collection_name=COLLECTION_NAME
    )
    storage_service.initialize()

    chat = ChatService(llm, storage_service)
    chat.add_metadata_filter("document_name", "ECA2021_Digital")
    chat.generate_response("No que consiste a prestação de serviços comunitários?")

    '''
    docs = storage_service.similarity_search(
        "Qual o artigo 19 do Esatuto da Criança e do Adolescente?",
        k=10
    )
    '''

    #test = RAGEvaluator(llm, storage_service)
    #test.evaluate_rag(5)
    return 

if __name__ == "__main__":
    main()

#TODO Ignorar o modelo baixado +  Adicionar o git ignore + ignorar a pasta do modelo + Adicionar o modelo baixado no readme + Adicionar o modelo baixado no requirements.txt