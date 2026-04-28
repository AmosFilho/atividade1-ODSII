from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.chat import TriageDecision


@dataclass(frozen=True)
class TriageRule:
    action: str
    reason: str
    patterns: tuple[str, ...]
    requires_human: bool = False
    is_emergency: bool = False


TRIAGE_RULES = (
    TriageRule(
        action="urgencia_emergencia",
        reason="A pergunta relata sinal de alerta ou possivel urgencia.",
        patterns=(
            r"\bfalta de ar\b",
            r"\bdor no peito\b",
            r"\bdesma(i|iei|ou|ando)\b",
            r"\bconfus[aã]o mental\b",
            r"\bl[aá]bios? (arroxeados?|roxos?)\b",
            r"\bsangramento (intenso|muito|forte|persistente)\b",
            r"\bvomit(o|ei|ou|ando).{0,30}sangue\b",
            r"\bfezes pretas\b",
            r"\bfebre (persistente|alta)\b",
            r"\bdor abdominal (forte|intensa|progressiva)\b",
            r"\bincha[cç]o (no rosto|na face|na garganta|de garganta|nos l[aá]bios)\b",
            r"\burtic[aá]ria extensa\b",
            r"\bpiora (importante|r[aá]pida)\b",
        ),
        requires_human=True,
        is_emergency=True,
    ),
    TriageRule(
        action="encaminhar_humano",
        reason="A pergunta envolve medicamento ou alteracao de tratamento.",
        patterns=(
            r"\bposso (parar|suspender|tomar|dobrar|trocar|ajustar|manter)\b.{0,40}\b(rem[eé]dio|medicamento|medica[cç][aã]o)\b",
            r"\b(suspender|parar|ajustar|trocar|dobrar) (o|a|meu|minha)?\s*(rem[eé]dio|medicamento|dose)\b",
            r"\banticoagulante\b",
            r"\bantiagregante\b",
            r"\bclopidogrel\b",
            r"\bvarfarina\b",
            r"\brivaroxabana\b",
            r"\bapixabana\b",
            r"\bdabigatrana\b",
            r"\binsulina\b",
            r"\bmetformina\b",
        ),
        requires_human=True,
    ),
    TriageRule(
        action="encaminhar_humano",
        reason="A pergunta envolve condicao clinica que exige confirmacao individual.",
        patterns=(
            r"\bgr[aá]vid[ao]\b",
            r"\bgestante\b",
            r"\bamamentando\b",
            r"\bal[eé]rgic[ao]\b",
            r"\balergia\b",
            r"\bdiabetes\b",
            r"\bmarcapasso\b",
            r"\bdesfibrilador\b",
            r"\bdoen[cç]a renal\b",
            r"\bdial[ií]se\b",
            r"\bapneia do sono\b",
            r"\bdoen[cç]a card[ií]aca\b",
        ),
        requires_human=True,
    ),
    TriageRule(
        action="operacional_com_confirmacao",
        reason="A pergunta envolve preparo incompleto, divergente ou situacao operacional que a clinica deve confirmar.",
        patterns=(
            r"\bquebrei o jejum\b",
            r"\bcomi\b.{0,40}\b(hoje|agora|sem querer|antes do exame)\b",
            r"\bbebi\b.{0,40}\b(hoje|agora|sem querer|antes do exame)\b",
            r"\besqueci\b.{0,40}\b(preparo|laxante|dose|tomar)\b",
            r"\bvomitei\b.{0,40}\b(preparo|laxante)\b",
            r"\bn[aã]o consegui\b.{0,40}\b(evacuar|tomar|fazer o preparo)\b",
            r"\batrasad[ao]\b",
            r"\bsem acompanhante\b",
        ),
        requires_human=True,
    ),
)


def triage_question(question: str) -> TriageDecision:
    normalized = normalize(question)
    for rule in TRIAGE_RULES:
        if any(re.search(pattern, normalized) for pattern in rule.patterns):
            return TriageDecision(
                action=rule.action,
                reason=rule.reason,
                requires_human=rule.requires_human,
                is_emergency=rule.is_emergency,
            )

    return TriageDecision(
        action="operacional_responder",
        reason="A pergunta parece operacional e pode ser respondida com a base de conhecimento.",
    )


def normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def build_triage_answer(decision: TriageDecision) -> str | None:
    if decision.action == "urgencia_emergencia":
        return (
            "Pelo que voce descreveu, isso pode envolver um sinal de alerta. "
            "Nao e seguro tentar resolver por aqui.\n\n"
            "Entre em contato imediatamente com a clinica, com o medico responsavel "
            "ou procure um servico de urgencia/emergencia. Se houver falta de ar, "
            "dor no peito, desmaio, sangramento intenso ou piora rapida, procure "
            "atendimento de emergencia agora."
        )

    if decision.action == "encaminhar_humano":
        return (
            "Essa duvida precisa ser confirmada pela equipe da clinica ou pelo medico responsavel. "
            "Nao e seguro orientar individualmente por aqui.\n\n"
            "Nao suspenda, inicie, troque dose ou ajuste medicamentos por conta propria. "
            "Vou tratar isso como caso para atendimento humano."
        )

    return None
