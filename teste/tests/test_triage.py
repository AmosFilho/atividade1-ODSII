from app.rag.triage import build_triage_answer, triage_question


def test_triage_emergency_signs() -> None:
    decision = triage_question("Estou com dor abdominal forte e febre alta depois da colonoscopia")

    assert decision.action == "urgencia_emergencia"
    assert decision.requires_human is True
    assert decision.is_emergency is True
    assert build_triage_answer(decision) is not None


def test_triage_medication_goes_to_human() -> None:
    decision = triage_question("Posso suspender meu anticoagulante antes do exame?")

    assert decision.action == "encaminhar_humano"
    assert decision.requires_human is True
    assert decision.is_emergency is False
    assert "Nao suspenda" in (build_triage_answer(decision) or "")


def test_triage_operational_confirmation() -> None:
    decision = triage_question("Comi sem querer antes do exame, posso ir mesmo assim?")

    assert decision.action == "operacional_com_confirmacao"
    assert decision.requires_human is True
    assert build_triage_answer(decision) is None


def test_triage_operational_answer() -> None:
    decision = triage_question("Preciso levar documento com foto?")

    assert decision.action == "operacional_responder"
    assert decision.requires_human is False
