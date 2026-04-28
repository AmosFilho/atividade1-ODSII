from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass
from typing import Any

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_WHATSAPP_TEXT_LENGTH = 4096
REQUEST_TIMEOUT_SECONDS = 30
FALLBACK_WHATSAPP_TEXT = "Nao consegui gerar uma resposta."
CHATPRO_RECEIVED_EVENT = "received_message"
CHATPRO_LEGACY_EVENTS = {"send_message", "receive_message", "received_message", "receveid_message"}


@dataclass(frozen=True)
class WhatsAppInboundMessage:
    message_id: str
    from_number: str
    text: str


class WhatsAppClient:
    def __init__(
        self,
        access_token: str | None = None,
        phone_number_id: str | None = None,
        graph_api_version: str | None = None,
    ) -> None:
        self.access_token = access_token or settings.whatsapp_access_token
        self.phone_number_id = phone_number_id or settings.whatsapp_phone_number_id
        self.graph_api_version = graph_api_version or settings.whatsapp_graph_api_version

    @property
    def messages_url(self) -> str:
        if not self.phone_number_id:
            raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID nao configurado.")
        return f"https://graph.facebook.com/{self.graph_api_version}/{self.phone_number_id}/messages"

    def send_text(self, to: str, text: str) -> None:
        if not self.access_token:
            raise RuntimeError("WHATSAPP_ACCESS_TOKEN nao configurado.")

        for chunk in split_whatsapp_text(text):
            response = requests.post(
                self.messages_url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "text",
                    "text": {
                        "preview_url": False,
                        "body": chunk,
                    },
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()


class ChatProClient:
    def __init__(
        self,
        base_url: str | None = None,
        instance_id: str | None = None,
        token: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.chatpro_base_url).rstrip("/")
        self.instance_id = instance_id or settings.chatpro_instance_id
        self.token = token or settings.chatpro_token

    @property
    def send_message_url(self) -> str:
        if not self.instance_id:
            raise RuntimeError("CHATPRO_INSTANCE_ID nao configurado.")
        return f"{self.base_url}/{self.instance_id}/api/v1/send_message"

    def send_text(self, to: str, text: str) -> None:
        if not self.token:
            raise RuntimeError("CHATPRO_TOKEN nao configurado.")

        number = normalize_chatpro_number(to)
        prefixed_text = add_chatpro_bot_prefix(text)
        for chunk in split_whatsapp_text(prefixed_text):
            response = requests.post(
                self.send_message_url,
                headers={
                    "Authorization": self.token,
                    "Content-Type": "application/json",
                },
                json={
                    "number": number,
                    "message": chunk,
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()


def split_whatsapp_text(text: str) -> list[str]:
    clean_text = text.strip() or FALLBACK_WHATSAPP_TEXT
    if len(clean_text) <= MAX_WHATSAPP_TEXT_LENGTH:
        return [clean_text]

    chunks: list[str] = []
    remaining = clean_text
    while remaining:
        chunk = remaining[:MAX_WHATSAPP_TEXT_LENGTH]
        split_at = chunk.rfind("\n\n")
        if split_at < MAX_WHATSAPP_TEXT_LENGTH // 2:
            split_at = chunk.rfind(" ")
        if split_at < MAX_WHATSAPP_TEXT_LENGTH // 2:
            split_at = MAX_WHATSAPP_TEXT_LENGTH
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    return chunks


def parse_inbound_messages(payload: dict[str, Any] | list[Any]) -> list[WhatsAppInboundMessage]:
    if isinstance(payload, list):
        messages: list[WhatsAppInboundMessage] = []
        for item in payload:
            if isinstance(item, dict):
                messages.extend(parse_inbound_messages(item))
        if not messages:
            logger.info("parse_inbound_messages: Nenhuma mensagem encontrada no payload list: %r", payload)
        return messages

    chatpro_message = parse_chatpro_inbound_message(payload)
    if chatpro_message is not None:
        return [chatpro_message]

    chatpro_legacy_message = parse_chatpro_legacy_message(payload)
    if chatpro_legacy_message is not None:
        return [chatpro_legacy_message]

    messages: list[WhatsAppInboundMessage] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                text = message.get("text", {}).get("body")
                from_number = message.get("from")
                message_id = message.get("id")
                if not text or not from_number or not message_id:
                    continue
                messages.append(
                    WhatsAppInboundMessage(
                        message_id=str(message_id),
                        from_number=str(from_number),
                        text=str(text),
                    )
                )
    if not messages:
        logger.info("parse_inbound_messages: Nenhuma mensagem encontrada no payload dict: %r", payload)
    return messages


def parse_chatpro_inbound_message(payload: dict[str, Any]) -> WhatsAppInboundMessage | None:
    if payload.get("event") != CHATPRO_RECEIVED_EVENT:
        return None

    message_data = payload.get("message_data")
    if not isinstance(message_data, dict):
        return None

    if message_data.get("ignore") is True:
        logger.info("Mensagem ChatPro ignorada porque ignore=true.")
        return None

    text = clean_message_text(message_data.get("message"))
    if text and is_chatpro_bot_message(text):
        logger.info("Mensagem ChatPro ignorada porque parece ter sido enviada pelo bot.")
        return None

    from_me = message_data.get("from_me") is True
    if from_me and should_ignore_connected_number_message(text or ""):
        return None

    from_number = message_data.get("number") or message_data.get("participant")
    message_id = message_data.get("id")
    if not text or not from_number or not message_id:
        logger.info(
            "Mensagem ChatPro ignorada por campos ausentes: has_text=%s has_number=%s has_id=%s",
            bool(text),
            bool(from_number),
            bool(message_id),
        )
        return None

    return WhatsAppInboundMessage(
        message_id=str(message_id),
        from_number=normalize_chatpro_number(str(from_number)),
        text=strip_assistant_command(text) if from_me else text,
    )


def parse_chatpro_legacy_message(payload: dict[str, Any]) -> WhatsAppInboundMessage | None:
    event_type = payload.get("Type")
    if event_type not in CHATPRO_LEGACY_EVENTS:
        return None

    body = payload.get("Body")
    if not isinstance(body, dict):
        return None

    info = body.get("Info")
    if not isinstance(info, dict):
        return None

    text = clean_message_text(body.get("Text"))

    if is_chatpro_bot_message(str(text or "")):
        logger.info("Mensagem ChatPro ignorada porque parece ter sido enviada pelo bot.")
        return None

    from_me = info.get("FromMe") is True
    if from_me and should_ignore_connected_number_message(text or ""):
        return None

    message_id = info.get("Id")
    remote_jid = info.get("RemoteJid")
    sender_jid = info.get("SenderJid")
    from_number = remote_jid or sender_jid

    if not text or not from_number or not message_id:
        logger.info(
            "Mensagem ChatPro legacy ignorada por campos ausentes: has_text=%s has_number=%s has_id=%s | text=%r from_number=%r message_id=%r",
            bool(text),
            bool(from_number),
            bool(message_id),
            text,
            from_number,
            message_id,
        )
        return None

    clean_text = strip_assistant_command(text) if from_me else text
    return WhatsAppInboundMessage(
        message_id=str(message_id),
        from_number=normalize_chatpro_number(str(from_number)),
        text=clean_text,
    )


def clean_message_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_chatpro_number(value: str) -> str:
    number = value.split("@", maxsplit=1)[0]
    return "".join(char for char in number if char.isdigit())


def add_chatpro_bot_prefix(text: str) -> str:
    prefix = settings.chatpro_bot_prefix.strip()
    if not prefix:
        return text
    if text.strip().startswith(prefix):
        return text
    return f"{prefix}\n{text}"


def is_chatpro_bot_message(text: str) -> bool:
    prefix = settings.chatpro_bot_prefix.strip()
    return bool(prefix) and text.strip().startswith(prefix)


def should_ignore_connected_number_message(text: str) -> bool:
    if not settings.chatpro_respond_from_me:
        logger.info("Mensagem ChatPro ignorada porque veio do proprio numero conectado.")
        return True

    if not has_assistant_command(text):
        logger.info("Mensagem ChatPro ignorada porque veio do proprio numero conectado sem comando do assistente.")
        return True

    return False


def has_assistant_command(text: str) -> bool:
    trigger = settings.assistant_command_trigger.strip()
    clean_text = text.strip()
    return not trigger or clean_text.casefold().startswith(trigger.casefold())


def strip_assistant_command(text: str) -> str:
    trigger = settings.assistant_command_trigger.strip()
    clean_text = text.strip()
    if trigger and clean_text.casefold().startswith(trigger.casefold()):
        return clean_text[len(trigger) :].strip()
    return clean_text


def get_whatsapp_sender() -> WhatsAppClient | ChatProClient:
    if settings.whatsapp_provider.lower() == "chatpro":
        return ChatProClient()
    return WhatsAppClient()


def verify_webhook_signature(raw_body: bytes, signature_header: str | None) -> bool:
    if not settings.whatsapp_app_secret:
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        settings.whatsapp_app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)
