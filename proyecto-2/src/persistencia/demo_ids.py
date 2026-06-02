"""Identificadores ficticios de la semilla demo TAAM (TASK-114)."""

from __future__ import annotations

# Placeholders para panel de seguimiento; no son chat_id validos en Bot API.
CHAT_TELEGRAM_CASO_A = 111111111
CHAT_TELEGRAM_CASO_B = 222222222

_CHATS_DEMO_FICTICIOS = frozenset({CHAT_TELEGRAM_CASO_A, CHAT_TELEGRAM_CASO_B})


def es_chat_id_demo_ficticio(chat_id: int) -> bool:
    """True si el chat_id es solo de la semilla demo (no existe en Telegram)."""
    return chat_id in _CHATS_DEMO_FICTICIOS
