
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
import streamlit as st

MODEL_ID = "gemma-4-E2B-it-BF16.gguf"
REPO_ID = "unsloth/gemma-4-E2B-it-GGUF"
MODEL_PATH = "models/gemma-4-E2B-it-Q4_K_M.gguf"
PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "oberon"

@st.cache_resource
def load_llm():
    with st.spinner("Carregando modelo..."):
        return LLMService()
    

@st.cache_resource
def load_index(_llm):
    with st.spinner("Indexando documentos..."):
        storage = IndexService(
            llm_service=_llm,
            persist_dir=PERSIST_DIR,
            collection_name=COLLECTION_NAME
        )
        storage.initialize()
        return storage

@st.cache_resource
def load_chat(_llm, _index):
    chat = ChatService(_llm, _index)
    chat.add_metadata_filter(
        "document_name",
        "ECA2021_Digital"
    )

    return chat

def main():
    
    st.title("RAG System - Assitente dos Direitos do Cidadão")
    status = st.empty()
    
    llm = load_llm()

    #llm.generate_response("Olá, qual é a capital da França?")
    #llm.create_embedding("Olá, tudo bem?")
    storage_service = load_index(llm)
    #storage_service.initialize()
    chat = load_chat(llm, storage_service)
    #chat.add_metadata_filter("document_name", "ECA2021_Digital")
    status.toast("Sistema pronto.")
    user_query = st.chat_input("Digite sua pergunta aqui...")
    if user_query:
        with st.chat_message("user"):
            st.write(user_query)
        with st.spinner("Gerando resposta..."):
            response = chat.generate_response(user_query)
            #st.write("Resposta : ",response)
        with st.chat_message("assistant"):
            st.write(response)
    #test = RAGEvaluator(llm, storage_service)
    #test.evaluate_rag(5)
    return 

if __name__ == "__main__":
    main()

#TODO Ignorar o modelo baixado +  Adicionar o git ignore + ignorar a pasta do modelo + Adicionar o modelo baixado no readme + Adicionar o modelo baixado no requirements.txt