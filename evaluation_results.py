from langchain_community.chat_models import ChatOllama
from llm_service import LLMService
from index_service import IndexService

class RAGEvaluator:
    def __init__(self, llm_service: LLMService, storage_service: IndexService):
        self.llm_service = llm_service
        self.storage_index = storage_service

        # 👇 modelo avaliador
        self.judge_llm = ChatOllama(
            model="llama3",
            temperature=0
        )

    def evaluate_rag(self, top_k: int = 5):
        results = []

        for item in PERGUNTAS:
            query = item["question"]
            ground_truth = item["ground_truth"]

            # 🔍 Retrieval
            search_result = self.storage_index.similarity_search(query, top_k)
            retrieval_content = [doc.page_content for doc in search_result]

            # 🔁 Rerank
            reranked_docs = self.llm_service.rerank(query, search_result)
            reranked_text = "\n\n".join([doc.page_content for doc in reranked_docs])

            # 🤖 Resposta do RAG
            system_instructions = """
            Você é uma assistente jurídica especializada no ECA.
            Responda SOMENTE com base no contexto.
            """

            full_user_prompt = f"Contexto:\n{reranked_text}\n\nPergunta:\n{query}"

            answer = self.llm_service.ask(
                system_prompt=system_instructions,
                user_query=full_user_prompt
            )

            # ⚖️ Avaliação pelo LLM
            eval_prompt = f"""
            Avalie a resposta de um sistema RAG.

            Pergunta:
            {query}

            Resposta esperada:
            {ground_truth}

            Resposta gerada:
            {answer}

            Critérios:
            - 1.0 = totalmente correta
            - 0.5 = parcialmente correta
            - 0.0 = incorreta

            Responda no formato:
            Score: <0.0 a 1.0>
            Justificativa: <explique brevemente>
            """

            evaluation = self.judge_llm.invoke(eval_prompt).content

            results.append({
                "question": query,
                "ground_truth": ground_truth,
                "answer": answer,
                "evaluation": evaluation
            })

        # 📊 Print bonito
        total_score = 0
        for r in results:
            print("\n" + "="*50)
            print(f"Pergunta: {r['question']}")
            print(f"Resposta: {r['answer']}")
            print(f"Esperado: {r['ground_truth']}")
            print(f"Avaliação:\n{r['evaluation']}")

            # tentativa simples de extrair score
            if "Score:" in r["evaluation"]:
                try:
                    score = float(r["evaluation"].split("Score:")[1].split()[0])
                    total_score += score
                except:
                    pass

        avg_score = total_score / len(results)
        print("\n" + "="*50)
        print(f"Score médio: {avg_score:.2f}")

        return results
PERGUNTAS = [
    {
        "question":
        "No que consiste a prestação de serviços comunitários no ECA?",
        # CORRETO: ✅
        "ground_truth":
        "Realização de tarefas gratuitas de interesse geral",
        # ERRADO: ❌
        # Trabalho remunerado obrigatório
    }
    ,
    {
        "question":
        "Qual é a idade máxima considerada para adolescente no ECA?",
        # CORRETO: ✅
        "ground_truth":
        "18 anos incompletos",
        # ERRADO: ❌
        # 21 anos
    }
    ,
    {
        "question":
        "Qual medida socioeducativa prevê permanência em estabelecimento educacional?",
        # CORRETO: ✅
        "ground_truth":
        "Internação",
        # ERRADO: ❌
        # Liberdade assistida
    }
    
]

sample_queries = [
    "No que consiste a prestação de serviços comunitários no ECA?",
    "Qual é a idade máxima considerada para adolescente no ECA?",
    "Qual medida socioeducativa prevê permanência em estabelecimento educacional?"
]

expected_responses = [
    "Realização de tarefas gratuitas de interesse geral",
    "18 anos incompletos",
    "Internação"
]