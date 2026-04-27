from llm_service import LLMService
from index_service import IndexService
from chat_service import ChatService
import pandas as pd
from dotenv import load_dotenv
import json
import ast

load_dotenv()

async def evaluate_rag_system(llm: LLMService, 
                        index_store:IndexService,
                         chat_service: ChatService,
                           top_k_results:int):
    path_ods = "test_values.ods"

    reranker_model = llm.rerank_model
    loaded_dataset = load_evaluation_dataset(path_ods)
    for item in loaded_dataset:
        question = item["pergunta"]
        retieval_results = index_store.similarity_search(question, k=top_k_results)
        reranked_results = llm.rerank(question, retieval_results, top_n=top_k_results)
        retrieved_chunks = [
            doc.page_content[:500]
            for doc in reranked_results
        ]
        item["chunks_retornados"] = retrieved_chunks
        response = chat_service.generate_response_from_context(question, reranked_results[:5])
        item["resposta"] = response
        item["precisao_recuperacao"] = context_precision_crossencoder(
            query=question,
            retrieved_chunks=retrieved_chunks[:5],
            reranker=reranker_model
            
        )
        item["qualidade_resposta"] = faithfulness_score(
            reranker_model, 
            response, 
            retrieved_chunks[:5])
    out_df = pd.DataFrame(loaded_dataset)

    if "chunks_retornados" in out_df.columns:
        out_df["chunks_retornados"] = (
            out_df["chunks_retornados"]
            .apply(
                lambda x: ",".join(map(str, x))
                if isinstance(x, list)
                else x
            )
        )

    out_df.to_excel(
        path_ods,     
        engine="odf",
        index=False
    )


def context_precision_crossencoder(
    query,
    retrieved_chunks,
    reranker
):
    pairs = [
      [query, chunk]
      for chunk in retrieved_chunks
    ]

    scores = reranker.predict(
       pairs
    )

    return float(scores.mean())

def faithfulness_score(reranker, answer, retrieved_chunks):
    pairs = [
       [answer, chunk]
       for chunk in retrieved_chunks
    ]

    scores = reranker.predict(pairs)

    return float(scores.mean())

def load_evaluation_dataset(file_path: str):
    """
    Lê um arquivo .ods e devolve uma lista de registros.

    Estrutura retornada:
    [
        {
            "pergunta": ...,
            "resposta": ...,
            "resposta_esperada": ...,
            "chunks_retornados": [...],
            "precisao_recuperacao": ...,
            "qualidade_resposta": ...
        }
    ]
    """

    tabela = pd.read_excel(
        file_path,
        engine="odf"
    )

    dataset = []

    for _, linha in tabela.iterrows():

        chunks = []

        if pd.notna(linha["chunks_retornados"]):
            raw = str(linha["chunks_retornados"]).strip()
            try:
                chunks = json.loads(raw)

            except json.JSONDecodeError:
                try:
                    chunks = ast.literal_eval(raw)

                except Exception:
                    chunks = raw.split(",")
        registro = {
            "pergunta": linha["pergunta"],
            "resposta": linha["resposta"],
            "resposta_esperada": linha["resposta_esperada"],
            "chunks_retornados": chunks,
            "precisao_recuperacao": linha["precisao_recuperacao"],
            "qualidade_resposta": linha["qualidade_resposta"]
        }

        dataset.append(registro)

    return dataset

def atualizar_arquivo_ods(
    dataset,
    caminho_saida="avaliacao_atualizada.ods"
):
    """
    Escreve a estrutura atualizada em um .ods
    """

    linhas = []

    for item in dataset:

        linhas.append({
            "Pergunta":
                item["pergunta"],

            "resposta":
                item["resposta"],

            "resposta esperada":
                item["resposta_esperada"],

            "chunks retornados":
                json.dumps(item["chunks_retornados"], ensure_ascii=False),

            "precisao da recuperação":
                item["precisao_recuperacao"],

            "qualidade da resposta":
                item["qualidade_resposta"]
        })


    df = pd.DataFrame(linhas)

    df.to_excel(
        caminho_saida,
        engine="odf",
        index=False
    )

    print(
      f"Arquivo atualizado salvo em {caminho_saida}"
    )