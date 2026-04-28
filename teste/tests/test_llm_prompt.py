from app.rag.llm import build_prompt
from app.schemas.chat import SourceChunk


def test_prompt_instructs_model_to_avoid_hallucination() -> None:
    source = SourceChunk(
        id="1",
        source_id="abc",
        filename="triagem_smartphones.md",
        page=2,
        chunk_index=0,
        text="Se o aparelho molhou, desligue, nao carregue e procure avaliacao tecnica.",
        score=0.9,
    )

    prompt = build_prompt("Meu celular molhou. Posso colocar para carregar?", [source])

    assert "Nao invente" in prompt
    assert "triagem_smartphones.md" in prompt
    assert "Meu celular molhou. Posso colocar para carregar?" in prompt
