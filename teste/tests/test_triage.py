from app.rag.triage import build_triage_answer, triage_question


def test_triage_emergency_signs() -> None:
    decision = triage_question("A bateria do celular esta estufada e com cheiro de queimado")

    assert decision.action == "risco_seguranca"
    assert decision.requires_human is True
    assert decision.is_emergency is True
    assert build_triage_answer(decision) is not None


def test_triage_budget_goes_to_human() -> None:
    decision = triage_question("Quanto custa para trocar a tela do iPhone?")

    assert decision.action == "encaminhar_humano"
    assert decision.requires_human is True
    assert decision.is_emergency is False
    assert "atendimento humano" in (build_triage_answer(decision) or "")


def test_triage_general_warranty_question_goes_to_rag() -> None:
    decision = triage_question("O que voce pode falar sobre garantia?")

    assert decision.action == "operacional_responder"
    assert decision.requires_human is False
    assert build_triage_answer(decision) is None


def test_triage_specific_warranty_question_goes_to_human() -> None:
    decision = triage_question("Minha garantia cobre tela quebrada?")

    assert decision.action == "encaminhar_humano"
    assert decision.requires_human is True


def test_triage_regular_defect_goes_to_rag() -> None:
    decision = triage_question("Meu notebook caiu e agora nao da imagem")

    assert decision.action == "operacional_responder"
    assert decision.requires_human is False
    assert build_triage_answer(decision) is None


def test_triage_operational_answer() -> None:
    decision = triage_question("Preciso levar o carregador junto?")

    assert decision.action == "operacional_responder"
    assert decision.requires_human is False


def test_triage_out_of_scope_returns_scope_feedback() -> None:
    decision = triage_question("Qual a previsao do tempo para amanha?")

    assert decision.action == "fora_escopo"
    assert decision.requires_human is False
    assert "assistencia tecnica" in (build_triage_answer(decision) or "")


def test_triage_capability_question_returns_scope_feedback() -> None:
    decision = triage_question("O que voce faz?")

    assert decision.action == "fora_escopo"
    assert build_triage_answer(decision) is not None
