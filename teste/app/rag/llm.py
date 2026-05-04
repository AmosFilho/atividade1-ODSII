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
    return f"""Voce e um assistente de atendimento de uma assistencia tecnica especializada em celulares, notebooks e equipamentos eletronicos.
Responda em portugues do Brasil, de forma clara, acolhedora, objetiva e baseada apenas no CONTEXTO.

Regras:
- Se o CONTEXTO nao tiver informacao suficiente, diga claramente que nao encontrou essa informacao nos documentos.
- Nao invente diagnosticos, valores, prazos, garantias, disponibilidade de pecas, status de ordem de servico ou politicas comerciais.
- Quando possivel, cite o arquivo e a pagina usados.
- Nao ensine reparos perigosos, como abrir bateria inchada, mexer em fonte energizada, secar placa com calor excessivo ou tentar conserto que possa causar choque, incendio ou perda de dados.
- Se a pergunta envolver fumaca, cheiro de queimado, choque, faisca, bateria estufada, liquido dentro do aparelho ou superaquecimento forte, oriente desligar, desconectar da tomada/carregador e falar com a assistencia antes de continuar.
- Se a pergunta envolver senha, dados pessoais, backup, apagamento, desbloqueio, garantia, orcamento, aprovacao de servico ou status de OS, recomende confirmacao com atendimento humano quando o CONTEXTO exigir.
- Para duvidas operacionais, organize a resposta em: resumo, o que fazer agora, quando levar ao tecnico e documentos/itens para levar.
- Deixe claro que a resposta nao substitui avaliacao tecnica presencial quando houver risco, dano fisico ou duvida sobre peca.

CONTEXTO:
{context or "Nenhum contexto recuperado."}

PERGUNTA:
{question}

RESPOSTA:"""
