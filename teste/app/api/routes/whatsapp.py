from __future__ import annotations

import logging

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.api.dependencies import get_rag_pipeline
from app.core.config import settings
from app.integrations.whatsapp import (
    get_whatsapp_sender,
    parse_inbound_messages,
    verify_webhook_signature,
)
from app.rag.pipeline import RAGPipeline
from app.schemas.chat import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])


@router.get("", response_class=PlainTextResponse)
def verify_whatsapp_webhook(
    mode: str | None = Query(default=None, alias="hub.mode"),
    verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> str:
    if (
        mode == "subscribe"
        and settings.whatsapp_verify_token
        and verify_token == settings.whatsapp_verify_token
        and challenge is not None
    ):
        return challenge
    raise HTTPException(status_code=403, detail="Token de verificacao invalido.")


@router.post("")
async def receive_whatsapp_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    rag: RAGPipeline = Depends(get_rag_pipeline),
) -> dict[str, str]:
    raw_body = await request.body()
    if not verify_webhook_signature(raw_body, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Assinatura invalida.")

    payload = await request.json()
    logger.info(
        "Webhook WhatsApp recebido: tipo_payload=%s resumo=%s",
        type(payload).__name__,
        summarize_webhook_payload(payload),
    )
    inbound_messages = parse_inbound_messages(payload)
    if not inbound_messages:
        logger.info("Webhook WhatsApp ignorado: nenhuma mensagem de texto de entrada encontrada.")
        return {"status": "ignored"}

    client = get_whatsapp_sender()
    for inbound in inbound_messages:
        logger.info("Mensagem WhatsApp recebida: id=%s from=%s", inbound.message_id, inbound.from_number)
        try:
            chat_response = rag.ask(ChatRequest(question=inbound.text))
            answer = format_whatsapp_answer(chat_response.answer, chat_response.triage.action if chat_response.triage else None)
            client.send_text(inbound.from_number, answer)
        except Exception:
            logger.exception("Falha ao processar mensagem WhatsApp id=%s", inbound.message_id)

    return {"status": "ok"}


def format_whatsapp_answer(answer: str, triage_action: str | None = None) -> str:
    if triage_action == "urgencia_emergencia":
        return f"Atencao: encaminhamento imediato recomendado.\n\n{answer}"
    if triage_action == "encaminhar_humano":
        return f"Atendimento humano recomendado.\n\n{answer}"
    if triage_action == "operacional_com_confirmacao":
        return f"Confirmacao com a clinica recomendada.\n\n{answer}"
    return answer


def summarize_webhook_payload(payload: Any) -> object:
    if isinstance(payload, list):
        return [summarize_webhook_payload(item) for item in payload[:5]]

    if not isinstance(payload, dict):
        return {"type": type(payload).__name__}

    summary: dict[str, object] = {
        "keys": sorted(str(key) for key in payload.keys())[:12],
    }
    for key in ("event", "Type", "type"):
        if key in payload:
            summary[key] = payload.get(key)

    message_data = payload.get("message_data")
    if isinstance(message_data, dict):
        summary["message_data"] = {
            "keys": sorted(str(key) for key in message_data.keys())[:16],
            "type": message_data.get("type"),
            "from_me": message_data.get("from_me"),
            "has_message": bool(message_data.get("message")),
            "has_number": bool(message_data.get("number")),
        }

    body = payload.get("Body")
    if isinstance(body, dict):
        summary["Body"] = {
            "keys": sorted(str(key) for key in body.keys())[:16],
            "has_Text": bool(body.get("Text")),
        }
        info = body.get("Info")
        if isinstance(info, dict):
            summary["Body"]["Info"] = {
                "keys": sorted(str(key) for key in info.keys())[:16],
                "FromMe": info.get("FromMe"),
                "has_RemoteJid": bool(info.get("RemoteJid")),
                "has_SenderJid": bool(info.get("SenderJid")),
            }

    return summary
