from __future__ import annotations

from app.schemas.chat import TriageDecision


SAFETY_TERMS = (
    "bateria estufada",
    "bateria inchada",
    "bateria inflada",
    "cheiro de queimado",
    "fumaca",
    "faisca",
    "pegou fogo",
    "choque",
    "curto",
    "superaqueceu",
    "superaquecendo",
    "superaquecimento",
)

HUMAN_TERMS = (
    "quanto custa",
    "preco",
    "valor",
    "orcamento",
    "desconto",
    "reembolso",
    "aprovar",
    "cancelar servico",
    "status",
    "ordem de servico",
    "numero da os",
    "senha",
    "desbloqueio",
    "desbloquear",
    "icloud",
    "conta google",
    "frp",
    "recuperar dados",
    "recuperar fotos",
)

SPECIFIC_WARRANTY_TERMS = (
    "minha garantia",
    "meu aparelho",
    "meu equipamento",
    "cobre",
    "acionar garantia",
    "garantia cobre",
    "garantia vale",
    "garantia venceu",
    "garantia acabou",
)

IN_SCOPE_TERMS = (
    "assistencia",
    "tecnico",
    "conserto",
    "reparo",
    "servico",
    "celular",
    "telefone",
    "smartphone",
    "iphone",
    "samsung",
    "motorola",
    "xiaomi",
    "tablet",
    "notebook",
    "computador",
    "pc",
    "monitor",
    "carregador",
    "cabo",
    "fonte",
    "bateria",
    "tela",
    "teclado",
    "placa",
    "conector",
    "liga",
    "carrega",
    "molhou",
    "caiu",
    "travando",
    "lento",
    "formatar",
    "backup",
    "garantia",
    "orcamento",
    "os",
    "ordem de servico",
    "prazo",
    "coleta",
    "entrega",
    "retirada",
    "nota fiscal",
    "documento",
    "loja",
    "endereco",
)

CAPABILITY_TERMS = (
    "o que voce faz",
    "o que vc faz",
    "como voce pode ajudar",
    "como vc pode ajudar",
    "com o que voce ajuda",
    "com o que vc ajuda",
    "quais perguntas",
    "qual seu escopo",
)

OUT_OF_SCOPE_TERMS = (
    "previsao do tempo",
    "clima",
    "futebol",
    "jogo de hoje",
    "noticia",
    "politica",
    "receita",
    "restaurante",
    "hotel",
    "passagem",
    "viagem",
    "filme",
    "musica",
    "remedio",
    "medicamento",
    "consulta medica",
    "dor de cabeca",
)


def triage_question(question: str) -> TriageDecision:
    normalized = normalize(question)

    if has_any(normalized, SAFETY_TERMS) or is_wet_device_still_powered(normalized):
        return TriageDecision(
            action="risco_seguranca",
            reason="A pergunta relata risco de seguranca eletrica, incendio, bateria ou dano imediato.",
            requires_human=True,
            is_emergency=True,
        )

    if is_scope_feedback_question(normalized):
        return TriageDecision(
            action="fora_escopo",
            reason="A pergunta nao parece estar dentro do escopo de assistencia tecnica.",
        )

    if has_any(normalized, HUMAN_TERMS) or has_specific_warranty_question(normalized):
        return TriageDecision(
            action="encaminhar_humano",
            reason="A pergunta envolve atendimento individual, valor, garantia especifica, OS, senha ou dados pessoais.",
            requires_human=True,
        )

    return TriageDecision(
        action="operacional_responder",
        reason="A pergunta pode ser respondida com a base de conhecimento.",
    )


def normalize(text: str) -> str:
    replacements = str.maketrans(
        {
            "á": "a",
            "à": "a",
            "â": "a",
            "ã": "a",
            "é": "e",
            "ê": "e",
            "í": "i",
            "ó": "o",
            "ô": "o",
            "õ": "o",
            "ú": "u",
            "ç": "c",
        }
    )
    return " ".join(text.lower().translate(replacements).strip().split())


def has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def is_wet_device_still_powered(text: str) -> bool:
    return ("molhou" in text or "caiu na agua" in text) and has_any(text, ("ligado", "carregando", "tomada"))


def has_specific_warranty_question(text: str) -> bool:
    if "garantia" not in text:
        return False
    return has_any(text, SPECIFIC_WARRANTY_TERMS)


def is_scope_feedback_question(text: str) -> bool:
    if not text:
        return True
    if has_any(text, CAPABILITY_TERMS):
        return True
    if has_any(text, OUT_OF_SCOPE_TERMS):
        return not has_any(text, IN_SCOPE_TERMS)
    return not has_any(text, IN_SCOPE_TERMS)


def build_triage_answer(decision: TriageDecision) -> str | None:
    if decision.action == "fora_escopo":
        return (
            "Posso ajudar com duvidas de assistencia tecnica: celulares, notebooks, carregamento, tela, "
            "bateria, aparelho molhado, garantia geral, orcamento, OS, coleta/entrega e itens para levar.\n\n"
            "Me diga qual e o equipamento e o problema que eu tento orientar com base nos documentos."
        )

    if decision.action == "risco_seguranca":
        return (
            "Pelo que voce descreveu, pode haver risco de choque, curto, incendio ou dano maior ao aparelho. "
            "Nao e seguro tentar resolver sozinho.\n\n"
            "Desligue o equipamento, desconecte da tomada/carregador e nao tente abrir, carregar ou aquecer. "
            "Fale com a assistencia tecnica para receber orientacao antes de continuar."
        )

    if decision.action == "encaminhar_humano":
        return (
            "Essa duvida precisa ser confirmada por um atendente da assistencia tecnica. "
            "Nao consigo validar valores, garantias especificas, status de ordem de servico, senhas ou dados pessoais por aqui.\n\n"
            "Vou tratar isso como caso para atendimento humano."
        )

    return None
