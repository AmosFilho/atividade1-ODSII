from __future__ import annotations

import requests

from app.core.config import settings
from app.schemas.chat import SourceChunk


class OllamaLLM:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout_seconds = timeout_seconds or settings.llm_timeout_seconds

    def generate(self, question: str, sources: list[SourceChunk]) -> str:
        prompt = build_prompt(question, sources)
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": build_ollama_options(),
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                "Nao foi possivel acessar o Ollama. Verifique se ele esta rodando "
                f"e se o modelo '{self.model}' foi baixado."
            ) from exc

        payload = response.json()
        return str(payload.get("response") or "").strip()


def build_ollama_options() -> dict[str, float | int]:
    options = {
        "temperature": settings.llm_temperature,
        "num_ctx": settings.llm_num_ctx,
        "num_predict": settings.llm_num_predict,
        "num_gpu": settings.llm_num_gpu,
    }
    return {key: value for key, value in options.items() if value is not None}


def build_prompt(question: str, sources: list[SourceChunk]) -> str:
    context = "\n\n".join(
        f"[Fonte {index}] arquivo={source.filename}; pagina={source.page or 'n/a'}; "
        f"chunk={source.chunk_index}\n{source.text}"
        for index, source in enumerate(sources, start=1)
    )
    return f"""Voce e um assistente de atendimento de clinica medica para orientacao pre e pos-procedimento.
Responda em portugues do Brasil, de forma clara, acolhedora, objetiva e baseada apenas no CONTEXTO.

Regras:
- Se o CONTEXTO nao tiver informacao suficiente, diga claramente que nao encontrou essa informacao nos documentos.
- Nao invente preparos, prazos, riscos, contraindicacoes, doses, suspensao de medicamentos ou condutas.
- Quando possivel, cite o arquivo e a pagina usados.
- Nao diagnostique, nao prescreva, nao altere medicacao e nao decida se o paciente esta apto para realizar um procedimento.
- Se a pergunta envolver sintoma grave, reacao importante, sangramento intenso, falta de ar, dor forte, desmaio, febre persistente ou piora importante, oriente contato imediato com a clinica, servico de urgencia ou emergencia.
- Se a pergunta envolver gravidez, alergia, anticoagulante, diabetes, doenca cardiaca, marcapasso, sedacao, crianca, idoso fragil ou comorbidade relevante, recomende confirmar com a equipe da clinica.
- Para duvidas operacionais, organize a resposta em: resumo, preparo/orientacao, quando falar com a clinica e documentos/itens para levar.
- Deixe claro que a resposta nao substitui orientacao da equipe de saude responsavel.

CONTEXTO:
{context or "Nenhum contexto recuperado."}

PERGUNTA:
{question}

RESPOSTA:"""
