"""Pruebas de enmascaramiento de chat_id Telegram."""

from __future__ import annotations

from src.privacidad import enmascarar_chat_id_telegram


def test_enmascarar_chat_id_largo() -> None:
    assert enmascarar_chat_id_telegram(123456789) == "*****6789"


def test_enmascarar_chat_id_corto() -> None:
    assert enmascarar_chat_id_telegram(1234) == "****"
    assert enmascarar_chat_id_telegram("99") == "****"


def test_enmascarar_chat_id_string() -> None:
    assert enmascarar_chat_id_telegram("9876543210") == "******3210"
