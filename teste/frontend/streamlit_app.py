import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="RAG Procedimentos Clinicos", layout="wide")

st.title("Assistente RAG de Orientacao Pre-Procedimento")
st.caption("Envie protocolos da clinica, instrucoes de preparo, termos e FAQs para responder duvidas operacionais de pacientes com seguranca.")


def api_get(path: str) -> requests.Response:
    return requests.get(f"{API_URL}{path}", timeout=30)


def api_post(path: str, **kwargs) -> requests.Response:
    return requests.post(f"{API_URL}{path}", timeout=180, **kwargs)


def api_delete(path: str) -> requests.Response:
    return requests.delete(f"{API_URL}{path}", timeout=60)


with st.sidebar:
    st.header("Base de conhecimento")

    uploaded_file = st.file_uploader("Enviar documento", type=["pdf", "txt", "md", "markdown", "html", "htm"])
    if uploaded_file and st.button("Indexar documento", use_container_width=True):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = api_post("/documents/upload", files=files)
        if response.ok:
            payload = response.json()
            st.success(f"{payload['chunks_indexed']} chunks indexados.")
        else:
            st.error(response.text)

    if st.button("Indexar exemplos", use_container_width=True):
        response = api_post("/documents/ingest-samples")
        if response.ok:
            payload = response.json()
            st.success(payload["message"])
        else:
            st.error(response.text)

    if st.button("Limpar base vetorial", use_container_width=True):
        response = api_delete("/documents")
        if response.ok:
            st.warning("Base vetorial limpa.")
        else:
            st.error(response.text)

    st.divider()
    st.subheader("Documentos indexados")
    try:
        response = api_get("/documents")
        if response.ok:
            documents = response.json()["documents"]
            if not documents:
                st.info("Nenhum documento indexado.")
            for document in documents:
                st.write(f"**{document['filename']}**")
                st.caption(f"{document['chunks']} chunks | id: {document['source_id'][:8]}")
        else:
            st.error(response.text)
    except requests.RequestException:
        st.error("API indisponivel. Inicie o FastAPI antes de usar a interface.")

question = st.text_area(
    "Pergunta",
    placeholder="Ex.: Tenho endoscopia amanha. Preciso ir acompanhado e fazer jejum?",
    height=100,
)

col1, col2 = st.columns([1, 4])
with col1:
    top_k = st.number_input("Fontes", min_value=1, max_value=10, value=4, step=1)
with col2:
    st.write("")
    st.write("")
    ask = st.button("Perguntar", type="primary", use_container_width=True)

if ask:
    if not question.strip():
        st.warning("Digite uma pergunta.")
    else:
        with st.spinner("Consultando documentos e gerando resposta..."):
            try:
                response = api_post("/chat", json={"question": question, "top_k": int(top_k)})
            except requests.RequestException:
                st.error("Nao foi possivel conectar na API.")
            else:
                if not response.ok:
                    st.error(response.text)
                else:
                    payload = response.json()
                    triage = payload.get("triage")
                    if triage:
                        action = triage["action"]
                        if triage.get("is_emergency"):
                            st.error("Encaminhamento imediato recomendado.")
                        elif triage.get("requires_human"):
                            st.warning("Atendimento humano recomendado.")
                        else:
                            st.info("Pergunta operacional.")
                        st.caption(f"Triagem: {action} | {triage['reason']}")

                    st.subheader("Resposta")
                    st.write(payload["answer"])

                    st.subheader("Fontes usadas")
                    if not payload["sources"]:
                        st.info("Nenhuma fonte recuperada para esta resposta.")
                    else:
                        for index, source in enumerate(payload["sources"], start=1):
                            page = source["page"] or "n/a"
                            score = source["score"]
                            score_label = f"{score:.2f}" if score is not None else "n/a"
                            with st.expander(
                                f"{index}. {source['filename']} | pagina {page} | score {score_label}"
                            ):
                                st.write(source["text"])
