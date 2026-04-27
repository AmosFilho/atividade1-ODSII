
from llm_service import LLMService
from index_service import IndexService
from chat_service import ChatService
from evaluation_results import evaluate_rag_system
import streamlit as st
import asyncio

MODEL_ID = "gemma-4-E2B-it-BF16.gguf"
REPO_ID = "unsloth/gemma-4-E2B-it-GGUF"
MODEL_PATH = "models/gemma-4-E2B-it-Q4_K_M.gguf"
PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "oberon"

PERGUNTAS = [
    {
        "question": "Em que ano foi sancionado o Estatuto da Criança e do Adolescente?",
        "ground_truth": "1990",
        "relevant_chunk": [8]
    },
    {
        "question": "Qual artigo da Constituição Federal é mencionado como base do ECA?",
        "ground_truth": "Artigo 227 da Constituição Federal",
        "relevant_chunk": [8]
    },
    {
        "question": "Segundo o trecho de apresentação do ECA, como crianças e adolescentes são definidos juridicamente?",
        "ground_truth": (
            "Como sujeitos de direitos, em condição peculiar de desenvolvimento "
            "e com prioridade absoluta"
        ),
        "relevant_chunk": [8]
    },
    {
        "question": "Segundo o trecho apresentado, quem é responsável por garantir o pleno desenvolvimento da criança e do adolescente?",
        "ground_truth": "Família, sociedade e Estado",
        "relevant_chunk": [8]
    },
    {
        "question": "Quais conselhos são citados como instâncias de controle das políticas públicas no Sistema de Garantia de Direitos?",
        "ground_truth": (
            "Conselhos municipais, estaduais, distrital e nacional dos direitos "
            "da criança e do adolescente"
        ),
        "relevant_chunk": [9]
    },
    {
        "question": "Segundo o trecho que menciona o CONANDA, qual estratégia é considerada fundamental para promover e defender os direitos de crianças e adolescentes?",
        "ground_truth": (
            "Fortalecimento e articulação entre os órgãos colegiados"
        ),
        "relevant_chunk": [9]
    },
    {
        "question": "No trecho que descreve a origem do Estatuto, de que tipo de construção o ECA é fruto?",
        "ground_truth": "Construção coletiva",
        "relevant_chunk": [10]
    },
    {
        "question": "No sumário exibido, em que ano foi promulgada a Lei do SINASE?",
        "ground_truth": "2012",
        "relevant_chunk": [5]
    },
    {
        "question": "No aviso de risco ao consumidor, o chamamento representa algum custo para o consumidor?",
        "ground_truth": "Não, não representa qualquer custo",
        "relevant_chunk": [951]
    },
    {
        "question": "Segundo o Art. 7º exibido, qual é o intervalo máximo dos relatórios periódicos de atendimento ao chamamento?",
        "ground_truth": "60 dias",
        "relevant_chunk": [953]
    },
    {
        "question": "Segundo o Art. 6º exibido, o que o fornecedor deve garantir ao consumidor após o chamamento?",
        "ground_truth": "Certificado de atendimento ao chamamento",
        "relevant_chunk": [952]
    },
    {
        "question": "Segundo o Art. 12 exibido, qual portaria foi revogada?",
        "ground_truth": "Portaria nº 789, de 24 de agosto de 2001",
        "relevant_chunk": [955]
    }
]

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

    storage_service = load_index(llm)
    chat = load_chat(llm, storage_service)
    status.toast("Sistema pronto.")
    user_query = st.chat_input("Digite sua pergunta aqui...")
    if user_query:
        with st.chat_message("user"):
            st.write(user_query)
        with st.spinner("Gerando resposta..."):
            response = chat.generate_response(user_query)
        with st.chat_message("assistant"):
            st.write(response)
    
    #Descomente a linha abaixo para rodar a avaliação do sistema RAG usando o dataset de avaliação
    #asyncio.run(evaluate_rag_system(llm, storage_service, chat, top_k_results=20))
    return 

if __name__ == "__main__":
    main()


