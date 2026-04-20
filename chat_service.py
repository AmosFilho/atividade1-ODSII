from llm_service import LLMService
from index_service import IndexService

TOP_K_RESULTS = 5

class ChatService:
    def __init__(self, llm_service: LLMService, storage_service: IndexService):
        self.llm = llm_service
        self.index_storage = storage_service
    def generate_response(self, query: str) -> None:
        # Here you would implement the logic to interact with the LLM model
        # For example, you might call an API or use a library function



        search_result = self.index_storage.similarity_search(query, TOP_K_RESULTS)
        context = "\n\n".join([doc.page_content for doc in search_result])

        response = self.llm.chat_model.create_chat_completion(
            messages = [
                {
                    "role":"system",
                    "content": """Você é uma assistente jurídica especializada no Estatuto da Criança e do Adolescente (ECA - Lei nº 8.069/1990).

                        Sua função é orientar o usuário com base na legislação, explicando de forma clara, objetiva e acessível.

                        Regras importantes:
                        - Responda SOMENTE com base no contexto fornecido.
                        - Não invente informações.
                        - Se a resposta não estiver no contexto, diga: "Não encontrei essa informação no Estatuto da Criança e do Adolescente."
                        - Sempre que possível, cite o artigo da lei.
                        """
                },
                {
                    "role": "user",
                    "content": f"Dado esse Contexto:\n{context}\n\n Responda a Pergunta:\n{query}"
                    
                }
            ],
            max_tokens=2000
        )
        print("Chegou aqui!")
        print(response["choices"][0]["message"]["content"])

        #print(context)
        return 


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
