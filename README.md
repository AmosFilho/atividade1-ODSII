# atividade1-ODSII

Este projeto é um sistema de Recuperação Guiada por Recuperação (RAG) voltado para ser um Assistente jurídico-informacional que permite ao cidadão consultar direitos, deveres e normas públicas a partir de documentos oficiais, utilizando recuperação semântica, reranking e geração de respostas com base em fontes.

O aplicativo carrega um modelo local de linguagem em português (`gemma-4-E2B-it-Q4_K_M.gguf`), indexa documentos PDF usando vetores de similaridade com Chroma e responde a perguntas em linguagem natural com base no conteúdo legal armazenado.

Componentes principais:
- `main.py`: interface em Streamlit para interação do usuário.
- `llm_service.py`: gerenciamento do modelo de linguagem, embeddings e reranking de documentos.
- `index_service.py`: criação e consulta do índice vetorial em Chroma.
- `chat_service.py`: fluxo de busca, reranking e geração de respostas baseadas no contexto retornado.
- `extract_documents.py`: extração e divisão de documentos PDF em chunks para indexação.

Objetivo:
- Permitir consultas a um acervo jurídico de forma interativa.
- Garantir respostas fundamentadas apenas no conteúdo indexado.
- Facilitar a análise de leis e normas para estudo ou avaliação.


## Como executar o projeto

### 1. Ative o ambiente virtual (se aplicável)

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Execute a aplicação

Inicie a interface com:

```bash
streamlit run main.py
```

O aplicativo abrirá no navegador (geralmente em `http://localhost:8501`) e permitirá consultas em linguagem natural sobre os documentos jurídicos indexados.

---

## Executando avaliação do sistema RAG (métricas)

O projeto inclui uma rotina de avaliação para medir a qualidade da recuperação e das respostas.

### 1. Abra `main.py`

Localize a linha:

```python
#asyncio.run(evaluate_rag_system(llm, storage_service, chat, top_k_results=20))
```

Descomente para:

```python
asyncio.run(
    evaluate_rag_system(
        llm,
        storage_service,
        chat,
        top_k_results=20
    )
)
```

### 2. Execute os testes

Rode novamente:

```bash
streamlit run main.py
```

A avaliação calculará métricas como:

- Precisão de recuperação (Context Precision)  
- Faithfulness / grounding da resposta  
- Qualidade da resposta

Os resultados serão salvos em:

```text
test_values.ods
```

para análise e comparação de desempenho do sistema RAG.

### 3. Voltar ao modo interativo

Após os testes, comente novamente:

```python
#asyncio.run(evaluate_rag_system(...))
```

para retornar ao uso normal do assistente.