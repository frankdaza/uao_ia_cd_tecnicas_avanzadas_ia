"""Pruebas del documento dashboard-openfang.md (sin secretos ni PHI)."""

from __future__ import annotations

import re
from pathlib import Path

_RUTA_DOC = Path(__file__).resolve().parents[1] / "docs" / "dashboard-openfang.md"
_PATRON_TOKEN = re.compile(r"\d{9,}:[A-Za-z0-9_-]{25,}")
# chat_id largo real (no el ficticio 900001 de 6 digitos)
_PATRON_CHAT_ID_LARGO = re.compile(r"telegram:\d{10,}")


def test_dashboard_doc_existe() -> None:
    assert _RUTA_DOC.is_file(), "Falta docs/dashboard-openfang.md"


def test_dashboard_doc_contenido_obligatorio() -> None:
    texto = _RUTA_DOC.read_text(encoding="utf-8").lower()
    for fragmento in (
        "127.0.0.1:4200",
        "openfang sessions",
        "openfang_home",
        "jq",
        "telegram:",
        "sessions/",
        "audit/hand_",
        "find",
        "telegram:900001",
        "logs/sessions.jsonl",
        "consultar_historial_sesion",
        "hand_recordatorio",
    ):
        assert fragmento in texto, f"Falta mencion de {fragmento!r} en el doc"


def test_dashboard_doc_prueba_negativa_openfang_home() -> None:
    texto = _RUTA_DOC.read_text(encoding="utf-8").lower()
    assert "openfang_home" in texto
    assert "mkdir" in texto or "inexistente" in texto
    assert "arrancar_dev" in texto


def test_dashboard_doc_sin_token_real() -> None:
    contenido = _RUTA_DOC.read_text(encoding="utf-8")
    assert not _PATRON_TOKEN.search(contenido)


def test_dashboard_doc_sin_chat_id_largo_sin_enmascarar() -> None:
    contenido = _RUTA_DOC.read_text(encoding="utf-8")
    assert not _PATRON_CHAT_ID_LARGO.search(contenido)
