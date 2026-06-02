"""Pruebas del documento telegram-bot-setup.md (sin secretos)."""

from __future__ import annotations

import re
from pathlib import Path

_RUTA_DOC = (
    Path(__file__).resolve().parents[1] / "docs" / "telegram-bot-setup.md"
)
# Token real BotFather: id largo + secreto >= 20 chars
_PATRON_TOKEN = re.compile(r"\d{9,}:[A-Za-z0-9_-]{25,}")


def test_doc_telegram_bot_setup_existe() -> None:
    assert _RUTA_DOC.is_file(), "Falta docs/telegram-bot-setup.md"


def test_doc_contenido_obligatorio() -> None:
    texto = _RUTA_DOC.read_text(encoding="utf-8").lower()
    for fragmento in (
        "botfather",
        "proyecto-2",
        "/start",
        "/help",
        "/version",
        "telegram_bot_token",
        "polling",
        "webhook",
    ):
        assert fragmento in texto, f"Falta mencion de {fragmento!r} en el doc"


def test_doc_sin_token_real() -> None:
    contenido = _RUTA_DOC.read_text(encoding="utf-8")
    assert not _PATRON_TOKEN.search(contenido)
