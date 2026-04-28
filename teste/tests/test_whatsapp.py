import hashlib
import hmac

from app.api.routes.whatsapp import format_whatsapp_answer
from app.core.config import settings
from app.integrations.whatsapp import (
    add_chatpro_bot_prefix,
    is_chatpro_bot_message,
    normalize_chatpro_number,
    parse_inbound_messages,
    should_ignore_connected_number_message,
    split_whatsapp_text,
    strip_assistant_command,
    verify_webhook_signature,
)


def test_parse_inbound_text_message() -> None:
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "wamid.123",
                                    "from": "5592999999999",
                                    "type": "text",
                                    "text": {"body": "Preciso levar acompanhante?"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    messages = parse_inbound_messages(payload)

    assert len(messages) == 1
    assert messages[0].message_id == "wamid.123"
    assert messages[0].from_number == "5592999999999"
    assert messages[0].text == "Preciso levar acompanhante?"


def test_parse_ignores_non_text_message() -> None:
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "wamid.123",
                                    "from": "5592999999999",
                                    "type": "image",
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    assert parse_inbound_messages(payload) == []


def test_parse_chatpro_received_message() -> None:
    payload = {
        "event": "received_message",
        "message_data": {
            "id": "ID131231231",
            "from_me": False,
            "ignore": False,
            "message": "Preciso fazer jejum?",
            "number": "5592999999999@s.whatsapp.net",
        },
    }

    messages = parse_inbound_messages(payload)

    assert len(messages) == 1
    assert messages[0].message_id == "ID131231231"
    assert messages[0].from_number == "5592999999999"
    assert messages[0].text == "Preciso fazer jejum?"


def test_parse_chatpro_received_message_list_payload() -> None:
    payload = [
        {
            "event": "sent_message",
            "message_data": {"id": "ignored"},
        },
        {
            "event": "received_message",
            "message_data": {
                "id": "ID131231232",
                "from_me": False,
                "ignore": False,
                "message": "Preciso levar documento?",
                "number": "5592888888888@s.whatsapp.net",
            },
        },
    ]

    messages = parse_inbound_messages(payload)

    assert len(messages) == 1
    assert messages[0].message_id == "ID131231232"
    assert messages[0].from_number == "5592888888888"
    assert messages[0].text == "Preciso levar documento?"


def test_parse_chatpro_ignores_from_me_by_default(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chatpro_respond_from_me", False)
    payload = {
        "event": "received_message",
        "message_data": {
            "id": "ID131231233",
            "from_me": True,
            "ignore": False,
            "message": "Mensagem enviada por mim",
            "number": "5592888888888@s.whatsapp.net",
        },
    }

    assert parse_inbound_messages(payload) == []


def test_parse_chatpro_allows_from_me_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chatpro_respond_from_me", True)
    monkeypatch.setattr(settings, "assistant_command_trigger", "!bot")
    payload = {
        "event": "received_message",
        "message_data": {
            "id": "ID131231234",
            "from_me": True,
            "ignore": False,
            "message": "!bot Mensagem de teste comigo mesmo",
            "number": "5592888888888@s.whatsapp.net",
        },
    }

    messages = parse_inbound_messages(payload)

    assert len(messages) == 1
    assert messages[0].text == "Mensagem de teste comigo mesmo"


def test_parse_chatpro_legacy_from_me_when_enabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chatpro_respond_from_me", True)
    monkeypatch.setattr(settings, "assistant_command_trigger", "!bot")
    payload = {
        "Type": "send_message",
        "Body": {
            "Text": "!bot Mensagem no formato legacy",
            "Info": {
                "Id": "3EB0447D78381969537E06",
                "FromMe": True,
                "RemoteJid": "5592888888888@s.whatsapp.net",
                "SenderJid": "5592999999999@s.whatsapp.net",
            },
        },
    }

    messages = parse_inbound_messages(payload)

    assert len(messages) == 1
    assert messages[0].from_number == "5592888888888"
    assert messages[0].text == "Mensagem no formato legacy"


def test_parse_chatpro_legacy_from_me_uses_configured_command(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chatpro_respond_from_me", True)
    monkeypatch.setattr(settings, "assistant_command_trigger", "!bo")
    payload = {
        "Type": "send_message",
        "Body": {
            "Text": "!bo Mensagem com gatilho configurado",
            "Info": {
                "Id": "3EB0447D78381969537E09",
                "FromMe": True,
                "RemoteJid": "5592888888888@s.whatsapp.net",
                "SenderJid": "5592999999999@s.whatsapp.net",
            },
        },
    }

    messages = parse_inbound_messages(payload)

    assert len(messages) == 1
    assert messages[0].text == "Mensagem com gatilho configurado"


def test_parse_chatpro_legacy_from_other_person() -> None:
    payload = {
        "Type": "send_message",
        "Body": {
            "Text": "Mensagem recebida de outra pessoa",
            "Info": {
                "Id": "3EB0447D78381969537E08",
                "FromMe": False,
                "RemoteJid": "5592888888888@s.whatsapp.net",
                "SenderJid": "5592999999999@s.whatsapp.net",
            },
        },
    }

    messages = parse_inbound_messages(payload)

    assert len(messages) == 1
    assert messages[0].from_number == "5592888888888"
    assert messages[0].text == "Mensagem recebida de outra pessoa"


def test_parse_chatpro_legacy_ignores_bot_message(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chatpro_respond_from_me", True)
    monkeypatch.setattr(settings, "chatpro_bot_prefix", "Assistente:")
    payload = {
        "Type": "send_message",
        "Body": {
            "Text": "Assistente:\nResposta automatica",
            "Info": {
                "Id": "3EB0447D78381969537E07",
                "FromMe": True,
                "RemoteJid": "5592888888888@s.whatsapp.net",
                "SenderJid": "5592999999999@s.whatsapp.net",
            },
        },
    }

    assert parse_inbound_messages(payload) == []


def test_chatpro_bot_prefix_helpers(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chatpro_bot_prefix", "Assistente:")

    text = add_chatpro_bot_prefix("Ola")

    assert text == "Assistente:\nOla"
    assert is_chatpro_bot_message(text) is True


def test_assistant_command_helpers(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chatpro_respond_from_me", True)
    monkeypatch.setattr(settings, "assistant_command_trigger", "!bot")

    assert should_ignore_connected_number_message("Mensagem normal") is True
    assert should_ignore_connected_number_message("!bot Mensagem normal") is False
    assert should_ignore_connected_number_message("!BoT Mensagem normal") is False
    assert strip_assistant_command("!bot Mensagem normal") == "Mensagem normal"
    assert strip_assistant_command("!BoT Mensagem normal") == "Mensagem normal"


def test_normalize_chatpro_number() -> None:
    assert normalize_chatpro_number("5592999999999@s.whatsapp.net") == "5592999999999"
    assert normalize_chatpro_number("+55 (92) 99999-9999") == "5592999999999"


def test_split_whatsapp_text_limits_chunks() -> None:
    chunks = split_whatsapp_text("a" * 5000)

    assert len(chunks) == 2
    assert all(len(chunk) <= 4096 for chunk in chunks)


def test_signature_verification_when_secret_is_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "whatsapp_app_secret", "secret")
    raw_body = b'{"hello":"world"}'
    digest = hmac.new(b"secret", raw_body, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(raw_body, f"sha256={digest}") is True
    assert verify_webhook_signature(raw_body, "sha256=invalid") is False


def test_format_whatsapp_answer_prefixes_handoff() -> None:
    text = format_whatsapp_answer("Nao suspenda medicamento.", "encaminhar_humano")

    assert text.startswith("Atendimento humano recomendado.")
