from llm_service import LLMService
from index_service import IndexService

TOP_K_RESULTS = 20
TOP_N_RERANK = 5

class ChatService:
    def __init__(self, llm_service: LLMService, storage_service: IndexService):
        self.llm = llm_service
        self.index_storage = storage_service
        self.active_metadata_filters = {}
    def generate_response(self, query: str) -> None:
        # Here you would implement the logic to interact with the LLM model
        # For example, you might call an API or use a library function
        search_result = self.index_storage.similarity_search(query, TOP_K_RESULTS, self.active_metadata_filters)
        reranked_docs  = self.llm.rerank(query, search_result, TOP_N_RERANK)
        context_text = "\n\n".join([doc.page_content for doc in reranked_docs])
        system_instructions = """
            Você é uma assistente jurídica especializada em documentos jurídicos com artigos da lei.

                Sua função é orientar o usuário com base na legislação, explicando de forma clara, objetiva e acessível.

                Regras importantes:
                - Responda SOMENTE com base no contexto fornecido.
                - Não invente informações.
                - Se a resposta não estiver no contexto, diga: "Não encontrei essa informação nos documentos armazenados."
                - Sempre que possível, cite o artigo da lei.
                
        """

        full_user_prompt = f"Dado esse contexto{context_text}\n\nResponda a Pergunta:\n{query}"
        
        answer = self.llm.ask(
            system_prompt=system_instructions,
            user_query=full_user_prompt
        )

        print("--- Resposta Final ---")
        print(answer)

    def add_metadata_filter(
        self,
        key:str,
        value
    ):
        self.active_metadata_filters[key] = value

    def clear_metadata_filters(self):
        self.active_metadata_filters = {}
