from app.rag.llm import build_prompt
from app.schemas.chat import SourceChunk


def test_prompt_instructs_model_to_avoid_hallucination() -> None:
    source = SourceChunk(
        id="1",
        source_id="abc",
        filename="protocolo_endoscopia.md",
        page=2,
        chunk_index=0,
        text="Para endoscopia com sedacao, o paciente deve comparecer com acompanhante adulto.",
        score=0.9,
    )

    prompt = build_prompt("Preciso levar acompanhante?", [source])

    assert "Nao invente" in prompt
    assert "protocolo_endoscopia.md" in prompt
    assert "Preciso levar acompanhante?" in prompt
