# Assistente RAG de Orientacao Pre-Procedimento

Aplicacao RAG para atendimento em clinicas medicas. O sistema responde duvidas operacionais de pacientes sobre preparo, documentos, horario de chegada, acompanhante, cuidados apos procedimento e sinais de alerta, usando apenas documentos indexados pela clinica.

> Este projeto nao substitui a equipe de saude. O bot nao diagnostica, nao prescreve, nao interpreta laudos, nao suspende medicamentos e nao decide se um paciente esta apto para realizar um procedimento.

## Objetivo

O projeto demonstra uma IA vertical para atendimento pre e pos-procedimento. Ele foi pensado para cenarios como:

- orientar pacientes sobre preparo para endoscopia, colonoscopia, ultrassom e exames de imagem;
- responder perguntas sobre jejum, sedacao, acompanhante, documentos e horario de chegada;
- encaminhar duvidas sensiveis para atendimento humano;
- orientar busca de urgencia/emergencia quando houver sinais de alerta;
- mostrar as fontes usadas na resposta para facilitar auditoria.

A base em `data/samples` e demonstrativa. Em uso real, os documentos devem ser substituidos ou revisados pela direcao tecnica da clinica.

## Ferramentas

- **API:** FastAPI
- **Interface:** Streamlit
- **LLM local:** Ollama, com `llama3.1:8b` por padrao
- **Embeddings:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **Banco vetorial:** ChromaDB persistente
- **Loader de documentos:** PDF, TXT, Markdown e HTML
- **Canal externo:** ChatPro API por padrao, com suporte opcional a WhatsApp Cloud API
- **Containerizacao:** Docker e Docker Compose
- **Testes:** pytest

## Arquitetura

```txt
frontend/streamlit_app.py
        |
        v
app/main.py  ->  app/api/routes/
        |
        v
app/rag/pipeline.py
        |
        +--> triage.py            classifica risco e necessidade de atendimento humano
        +--> document_loader.py   extrai texto de PDF/TXT/MD/HTML
        +--> text_splitter.py     divide documentos em chunks
        +--> embeddings.py        gera embeddings
        +--> vector_store.py      persiste e busca no ChromaDB
        +--> retriever.py         recupera fontes relevantes
        +--> llm.py               monta prompt e chama o Ollama
```

Estrutura principal:

```txt
app/
  api/routes/        Endpoints REST
  core/              Configuracao e logging
  rag/               Pipeline RAG
  schemas/           Modelos Pydantic
frontend/            Interface Streamlit
data/samples/        Base demonstrativa de protocolos clinicos
data/raw/            Uploads recebidos
data/vector_store/   ChromaDB persistente
evaluation/          Perguntas e scripts de avaliacao
tests/               Testes unitarios
```

## Configuracao

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Variaveis principais:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
CHROMA_COLLECTION=clinic_procedure_docs
CHUNK_SIZE=900
CHUNK_OVERLAP=150
TOP_K=4
LLM_NUM_CTX=2048
LLM_NUM_PREDICT=350
WHATSAPP_PROVIDER=chatpro
CHATPRO_INSTANCE_ID=
CHATPRO_TOKEN=
CHATPRO_BASE_URL=https://v5.chatpro.com.br
NGROK_AUTHTOKEN=
```

`LLM_NUM_CTX` limita a janela de contexto enviada ao modelo. `LLM_NUM_PREDICT` limita o tamanho maximo da resposta.

## Rodando Localmente

Crie e ative um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

No Windows:

```bash
.venv\Scripts\activate
```

Instale as dependencias:

```bash
pip install -r requirements.txt
```

Instale o Ollama, baixe o modelo e inicie o servidor:

```bash
ollama pull llama3.1:8b
ollama serve
```

Em outro terminal, inicie a API:

```bash
uvicorn app.main:app --reload
```

Em outro terminal, inicie a interface:

```bash
streamlit run frontend/streamlit_app.py
```

Acesse:

- API: `http://localhost:8000/docs`
- Interface: `http://localhost:8501`

Na interface, clique em **Indexar exemplos** antes de perguntar.

Pergunta de teste:

```txt
Tenho endoscopia com sedacao amanha. Preciso levar acompanhante?
```

## Rodando com Docker Compose

Suba API, frontend e Ollama:

```bash
docker compose up --build
```

Acesse:

- API: `http://localhost:8000/docs`
- Interface: `http://localhost:8501`
- Ollama: `http://localhost:11434`

O Compose usa um volume Docker para persistir os modelos do Ollama e monta o projeto em `/app` nos containers da API e do frontend.

### GPU NVIDIA

O servico `ollama` esta configurado com:

```yaml
gpus: all
```

Valide se a GPU esta disponivel dentro do container:

```bash
docker compose exec ollama nvidia-smi
```

## Endpoints

Documentacao interativa:

```txt
GET http://localhost:8000/docs
```

Principais rotas:

- `GET /health`
- `POST /documents/upload`
- `POST /documents/ingest-samples`
- `GET /documents`
- `DELETE /documents/{source_id}`
- `DELETE /documents`
- `POST /chat`
- `GET /webhooks/whatsapp`
- `POST /webhooks/whatsapp`

## WhatsApp

A integracao padrao usa ChatPro API. A integracao com a WhatsApp Cloud API da Meta tambem fica disponivel pelo mesmo webhook, mas o provider padrao do projeto e `chatpro`.

Fluxo:

```txt
Paciente no WhatsApp
        |
        v
ChatPro webhook
        |
        v
GET/POST /webhooks/whatsapp
        |
        v
triagem + RAGPipeline
        |
        v
resposta enviada pela API ChatPro
```

Variaveis:

```env
WHATSAPP_PROVIDER=chatpro
CHATPRO_INSTANCE_ID=chatpro-fx5qbe2hah
CHATPRO_TOKEN=token_da_instancia
CHATPRO_BASE_URL=https://v5.chatpro.com.br
CHATPRO_RESPOND_FROM_ME=false
CHATPRO_FROM_ME_TRIGGER=!bot
```

Webhook para configurar na instancia ChatPro:

```txt
https://SEU_DOMINIO/webhooks/whatsapp
```

Para desenvolvimento local, exponha a API com HTTPS publico:

```bash
docker compose up ngrok
```

O painel local do ngrok fica em:

```txt
http://localhost:4040
```

Copie a URL HTTPS exibida no painel e configure na ChatPro:

```txt
https://URL_DO_NGROK/webhooks/whatsapp
```

Para usar o container do ngrok, configure antes:

```env
NGROK_AUTHTOKEN=seu_token_do_ngrok
```

O `POST /webhooks/whatsapp` recebe mensagens de texto da ChatPro nos formatos `received_message` ou `Body.Text`, passa pela triagem, consulta o RAG quando apropriado e responde pelo endpoint `send_message`.

Por padrao, mensagens enviadas pelo proprio numero conectado sao ignoradas para evitar loops. Para testar conversando consigo mesmo, use temporariamente:

```env
CHATPRO_RESPOND_FROM_ME=true
CHATPRO_FROM_ME_TRIGGER=!bot
```

Nesse modo, apenas mensagens suas que comecem com `!bot` serao processadas. Exemplo:

```txt
!bot Tenho endoscopia amanha. Preciso levar acompanhante?
```

Se quiser usar a Cloud API oficial da Meta, altere:

```env
WHATSAPP_PROVIDER=meta
WHATSAPP_VERIFY_TOKEN=token_que_voce_configura_na_meta
WHATSAPP_ACCESS_TOKEN=token_de_acesso_da_meta
WHATSAPP_PHONE_NUMBER_ID=id_do_numero_no_whatsapp
WHATSAPP_GRAPH_API_VERSION=v20.0
WHATSAPP_APP_SECRET=app_secret_para_validar_assinatura
```

No provider `meta`, o `GET /webhooks/whatsapp` valida `hub.verify_token` e devolve `hub.challenge`.

Configure `WHATSAPP_APP_SECRET` em producao para validar o header `X-Hub-Signature-256`.

## Triagem e Handoff

Antes de consultar o RAG, a pergunta passa por uma triagem deterministica em `app/rag/triage.py`.

Classes de triagem:

- `operacional_responder`: pergunta operacional coberta pela base.
- `operacional_com_confirmacao`: o bot pode trazer informacao da base, mas recomenda confirmar com a clinica.
- `encaminhar_humano`: envolve medicamento, condicao especial ou decisao individual; o bot nao tenta resolver.
- `urgencia_emergencia`: relata sinal de alerta; orienta contato imediato com clinica, medico ou emergencia.

A resposta da API inclui o campo `triage`:

```json
{
  "answer": "...",
  "sources": [],
  "triage": {
    "action": "encaminhar_humano",
    "reason": "A pergunta envolve medicamento ou alteracao de tratamento.",
    "requires_human": true,
    "is_emergency": false
  }
}
```

## Avaliacao

As perguntas de avaliacao ficam em:

```txt
evaluation/questions.json
```

Avaliar recuperacao:

```bash
python -m evaluation.evaluate_retrieval
```

Avaliar respostas usando a API:

```bash
python -m evaluation.evaluate_answers
```

Critérios sugeridos para avaliacao manual:

- fidelidade ao contexto recuperado;
- ausencia de informacao inventada;
- citacao correta das fontes;
- encaminhamento adequado em sinais de alerta;
- recusa adequada de diagnostico, prescricao ou alteracao de medicamentos;
- classificacao correta da triagem e encaminhamento humano.

## Base de Conhecimento

Os documentos demonstrativos ficam em `data/samples`:

- `base_atendimento_seguro_clinica.md`
- `jejum_sedacao_e_acompanhante.md`
- `medicamentos_e_condicoes_especiais.md`
- `protocolo_endoscopia_digestiva.md`
- `protocolo_colonoscopia.md`
- `orientacoes_ultrassom_abdominal.md`
- `exames_imagem_contraste_e_mri.md`
- `sinais_alerta_pos_procedimento.md`

Cada arquivo inclui referencias usadas para calibracao. Em producao, substitua esses documentos pelos protocolos oficiais da clinica.

## Limites Atuais

- Nao ha OCR para PDFs escaneados.
- Nao ha autenticacao, auditoria, controle de acesso ou gestao de consentimento.
- A integracao com WhatsApp e inicial: recebe texto e responde; ainda nao ha fila humana, templates, persistencia de conversas ou controle de janela de 24 horas.
- Nao ha integracao com prontuario ou agenda.
- Nao ha revisao tecnica formal da base demonstrativa.
- O uso real em saude exige revisao clinica, adequacao LGPD, logs auditaveis e fluxo claro de atendimento humano.
